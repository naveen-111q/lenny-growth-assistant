import logging
import os
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.backend.models.db_models import Base

logger = logging.getLogger("lenny_growth.database")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

_engine = None
_SessionLocal = None
_active_dialect = "unknown"
_db_status_message = "Not initialized"


def initialize_database():
    """
    Initializes the database connection engine.
    Attempts to connect to PostgreSQL (settings.database_url).
    If unreachable, automatically falls back to SQLite for robust local dev/testing.
    """
    global _engine, _SessionLocal, _active_dialect, _db_status_message

    target_url = settings.database_url
    logger.info(f"Attempting to connect to primary database: {target_url.split('@')[-1] if '@' in target_url else target_url}")

    try:
        if target_url.startswith("postgresql"):
            # Test connection with short timeout
            test_engine = create_engine(target_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            _engine = test_engine
            _active_dialect = "postgresql"
            _db_status_message = "Connected to PostgreSQL"
            logger.info("Successfully connected to PostgreSQL database.")
        else:
            _engine = create_engine(target_url, connect_args={"check_same_thread": False})
            _active_dialect = "sqlite"
            _db_status_message = f"Connected to {target_url}"
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
        sqlite_fallback_url = "sqlite:///./data/lenny_assistant.db"
        _engine = create_engine(sqlite_fallback_url, connect_args={"check_same_thread": False})
        _active_dialect = "sqlite"
        _db_status_message = f"Fell back to SQLite ({sqlite_fallback_url}) due to PostgreSQL unavailability"

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # Automatically create tables if not existing
    try:
        Base.metadata.create_all(bind=_engine)
        logger.info(f"Database tables verified/created successfully using dialect: {_active_dialect}")
    except Exception as e:
        logger.error(f"Error creating database schema: {e}", exc_info=True)


# Initialize on import
initialize_database()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session.
    """
    global _SessionLocal
    if _SessionLocal is None:
        initialize_database()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> Tuple[bool, str, str]:
    """
    Checks database health. Returns (is_healthy, dialect, details).
    """
    global _engine, _active_dialect, _db_status_message
    if _engine is None:
        return False, "none", "Engine not initialized"
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, _active_dialect, _db_status_message
    except Exception as exc:
        return False, _active_dialect, f"Health check failed: {str(exc)}"
