import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.backend.database.session import initialize_database, get_db
from app.backend.routes import health_router, sessions_router, chat_router, generate_router
from app.rag.ingestion import ingest_transcripts

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("lenny_growth.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context:
    Initializes database schema and bootstraps transcript ingestion if needed.
    """
    logger.info("Starting up The Lenny Growth Assistant API...")
    initialize_database()

    # Automatically check if knowledge base needs bootstrapping
    db_gen = get_db()
    db = next(db_gen)
    try:
        count = ingest_transcripts(db, force=False)
        logger.info(f"Knowledge base ready with {count} transcript chunks.")
    except Exception as e:
        logger.error(f"Transcript bootstrapping warning: {e}")
    finally:
        db.close()

    yield
    logger.info("Shutting down The Lenny Growth Assistant API...")


app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Conversational product & growth AI assistant grounded in Lenny's Podcast transcripts.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Structured request logging middleware. Never logs secrets or sensitive body tokens.
    """
    start_time = time.time()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)
        logger.info(f"{method} {path} -> {response.status_code} ({process_time}ms)")
        return response
    except Exception as e:
        process_time = round((time.time() - start_time) * 1000, 2)
        logger.error(f"{method} {path} FAILED ({process_time}ms): {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please check application logs."}
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for structured input validation errors.
    """
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


# Register API Routers
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(generate_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to The Lenny Growth Assistant API",
        "docs_url": "/docs",
        "health_url": "/health",
        "active_provider": settings.llm_provider
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=False
    )
