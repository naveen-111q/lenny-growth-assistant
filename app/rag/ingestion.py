import os
import json
import logging
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.backend.database.session import initialize_database, get_db
from app.backend.models.db_models import TranscriptChunkModel
from app.rag.embeddings import embedding_service

logger = logging.getLogger("lenny_growth.ingestion")


def clean_text(text: str) -> str:
    """
    Cleans transcript text by normalizing whitespace, stripping non-printable chars,
    and removing artifacts.
    """
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 250, overlap: int = 40) -> List[str]:
    """
    Splits text into chunks of roughly `chunk_size` words with `overlap` words.
    Respects paragraph boundaries where possible.
    """
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        # If a single paragraph is longer than chunk_size, split by word window
        if len(words) > chunk_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0

            i = 0
            while i < len(words):
                end = min(i + chunk_size, len(words))
                sub_chunk = words[i:end]
                chunks.append(" ".join(sub_chunk))
                if end == len(words):
                    break
                i += (chunk_size - overlap)
            continue

        if current_length + len(words) <= chunk_size:
            current_chunk.extend(words)
            current_length += len(words)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                # Retain overlap from end of previous chunk
                overlap_words = current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
                current_chunk = list(overlap_words) + words
                current_length = len(current_chunk)
            else:
                current_chunk = words
                current_length = len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def load_transcripts_from_dir(directory_path: str = "data/transcripts") -> List[Dict[str, Any]]:
    """
    Reads all transcript JSON or TXT files from the specified directory.
    """
    transcripts = []
    if not os.path.exists(directory_path):
        logger.warning(f"Transcript directory '{directory_path}' does not exist.")
        return transcripts

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if not os.path.isfile(file_path):
            continue

        if filename.endswith(".json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    transcripts.append(data)
            except Exception as e:
                logger.error(f"Error parsing JSON transcript {filename}: {e}")
        elif filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    base_name = os.path.splitext(filename)[0]
                    transcripts.append({
                        "id": base_name,
                        "episode_title": base_name.replace("_", " ").title(),
                        "guest": "Lenny Podcast Guest",
                        "guest_role": "Expert",
                        "url": f"https://www.lennyspodcast.com/{base_name}/",
                        "content": content
                    })
            except Exception as e:
                logger.error(f"Error reading TXT transcript {filename}: {e}")

    return transcripts


def ingest_transcripts(db: Session, force: bool = False) -> int:
    """
    Loads, cleans, chunks, embeds, and stores transcripts in the database.
    Returns the total number of chunks stored.
    """
    existing_count = db.query(TranscriptChunkModel).count()
    if existing_count > 0 and not force:
        logger.info(f"Database already contains {existing_count} transcript chunks. Skipping ingestion (use force=True to re-index).")
        return existing_count

    if force:
        logger.info("Force re-indexing: clearing existing transcript chunks.")
        db.query(TranscriptChunkModel).delete()
        db.commit()

    transcripts = load_transcripts_from_dir()
    logger.info(f"Found {len(transcripts)} transcript files to ingest.")

    total_chunks_saved = 0
    all_chunks_to_embed = []
    chunk_records = []

    for t in transcripts:
        episode_id = t.get("id", "unknown_episode")
        episode_title = t.get("episode_title", "Untitled Episode")
        guest = t.get("guest", "Lenny's Guest")
        guest_role = t.get("guest_role", "")
        url = t.get("url", "")
        raw_content = t.get("content", "")

        cleaned = clean_text(raw_content)
        chunks = chunk_text(cleaned, chunk_size=200, overlap=35)

        for idx, text_chunk in enumerate(chunks):
            chunk_id = f"{episode_id}_{idx}"
            all_chunks_to_embed.append(text_chunk)
            chunk_records.append({
                "id": chunk_id,
                "episode_id": episode_id,
                "episode_title": episode_title,
                "guest": guest,
                "guest_role": guest_role,
                "url": url,
                "chunk_index": idx,
                "content": text_chunk
            })

    if not all_chunks_to_embed:
        logger.warning("No transcript content found to embed.")
        return 0

    logger.info(f"Generating embeddings for {len(all_chunks_to_embed)} chunks...")
    embeddings = embedding_service.embed_batch(all_chunks_to_embed)

    for record, emb in zip(chunk_records, embeddings):
        model_obj = TranscriptChunkModel(
            id=record["id"],
            episode_id=record["episode_id"],
            episode_title=record["episode_title"],
            guest=record["guest"],
            guest_role=record["guest_role"],
            url=record["url"],
            chunk_index=record["chunk_index"],
            content=record["content"],
            embedding=emb
        )
        db.merge(model_obj)
        total_chunks_saved += 1

    db.commit()
    logger.info(f"Successfully ingested {total_chunks_saved} transcript chunks into knowledge base.")
    return total_chunks_saved


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_database()
    db_gen = get_db()
    db = next(db_gen)
    try:
        count = ingest_transcripts(db, force=True)
        print(f"Ingested {count} chunks successfully.")
    finally:
        db.close()
