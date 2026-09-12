from app.backend.database.session import get_db
from app.rag.retrieval import retrieve_relevant_chunks, construct_grounded_context
from app.rag.ingestion import clean_text, chunk_text


def test_text_cleaning_and_chunking():
    dirty = "Hello   world!\r\n\r\n\r\nThis   is a    test."
    cleaned = clean_text(dirty)
    assert "Hello world!" in cleaned
    assert "\r" not in cleaned

    chunks = chunk_text("word " * 600, chunk_size=200, overlap=30)
    assert len(chunks) >= 3


def test_retrieval_pmf_topic():
    db_gen = get_db()
    db = next(db_gen)
    try:
        sources = retrieve_relevant_chunks(db, "How does Superhuman measure product market fit?", top_k=3, threshold=0.20)
        assert len(sources) > 0
        top_source = sources[0]
        assert "Rahul Vohra" in top_source.guest or "Product-Market Fit" in top_source.episode_title
        context = construct_grounded_context(sources)
        assert "Rahul Vohra" in context
    finally:
        db.close()


def test_retrieval_empty_on_irrelevant_query():
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Ask about a topic completely unrelated to Lenny's product podcasts with strict threshold
        sources = retrieve_relevant_chunks(
            db,
            "quantum chromodynamics quark gluon plasma subatomic particle decay",
            top_k=3,
            threshold=0.60
        )
        assert len(sources) == 0
    finally:
        db.close()
