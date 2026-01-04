import sqlite3
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import uuid


def get_db_path():
    return Path(__file__).parent.parent / "data" / "metadata" / "documents.db"


def get_qdrant_client():
    client = QdrantClient(path=Path(__file__).parent.parent / "data" / "qdrant_storage")
    return client


def log_event(conn, document_id: str, level: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (document_id, level, message) VALUES (?, ?, ?)",
        (document_id, level, message),
    )
    conn.commit()


def get_document_info(conn, document_id: str) -> Dict[str, any]:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT country, disease FROM documents WHERE document_id = ?", (document_id,)
    )
    row = cursor.fetchone()
    if row:
        return {"country": row[0], "disease": row[1]}
    return {"country": None, "disease": None}


def get_all_chunks(conn) -> List[Tuple]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT c.chunk_id, c.document_id, c.section, c.text, c.char_count
        FROM chunks c
        ORDER BY c.chunk_id
        """
    )
    return cursor.fetchall()


def get_unchunked_from_qdrant(qdrant_client, conn) -> List[Tuple]:
    all_chunks = get_all_chunks(conn)

    collection_name = "malaria_chunks"

    try:
        collections = qdrant_client.get_collections()
        collection_exists = any(
            col.name == collection_name for col in collections.collections
        )

        if not collection_exists:
            return all_chunks

        existing_chunk_ids = set()
        scroll_result = qdrant_client.scroll(
            collection_name=collection_name, limit=10000, with_payload=False
        )

        if scroll_result[0]:
            existing_chunk_ids = set(point.id for point in scroll_result[0])

        unchunked = [
            chunk for chunk in all_chunks if chunk[0] not in existing_chunk_ids
        ]
        return unchunked

    except Exception as e:
        return all_chunks


def create_qdrant_collection(qdrant_client, vector_size: int):
    collection_name = "malaria_chunks"

    collections = qdrant_client.get_collections()
    collection_exists = any(
        col.name == collection_name for col in collections.collections
    )

    if not collection_exists:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            optimizers_config={"indexing_threshold": 0},
        )
        print(f"Created Qdrant collection: {collection_name}")

    return collection_name


def load_semantic_model():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    return model


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def process_chunk_batch(
    qdrant_client,
    collection_name: str,
    semantic_model,
    chunks_batch: List[Tuple],
    document_cache: Dict[str, Dict],
    conn,
) -> Tuple[int, int]:
    success_count = 0
    error_count = 0

    chunk_ids = []
    vectors = []
    payloads = []

    for chunk_id, document_id, section, text, char_count in chunks_batch:
        try:
            if document_id not in document_cache:
                document_cache[document_id] = get_document_info(conn, document_id)

            doc_info = document_cache[document_id]

            semantic_embedding = semantic_model.encode(text)
            semantic_embedding = normalize_vector(semantic_embedding)

            chunk_ids.append(chunk_id)
            vectors.append(semantic_embedding.tolist())

            payload = {
                "document_id": document_id,
                "section": section,
                "char_count": char_count,
                "country": doc_info["country"],
                "disease": doc_info["disease"],
                "semantic_embedding_computed": True,
            }

            payloads.append(payload)
            success_count += 1

            log_event(
                conn,
                document_id,
                "INFO",
                f"Chunk {chunk_id}: semantic embedding computed, section={section}, chars={char_count}",
            )

        except Exception as e:
            error_count += 1
            log_event(
                conn,
                document_id,
                "ERROR",
                f"Chunk {chunk_id}: embedding failed - {str(e)}",
            )

    if chunk_ids:
        try:
            points = [
                PointStruct(id=chunk_id, vector=vector, payload=payload)
                for chunk_id, vector, payload in zip(chunk_ids, vectors, payloads)
            ]

            qdrant_client.upsert(collection_name=collection_name, points=points)

        except Exception as e:
            error_count += len(chunk_ids)
            log_event(conn, None, "ERROR", f"Batch upsert failed: {str(e)}")

    return success_count, error_count


def run_embedding():
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run create_db.py first."
        )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    qdrant_client = get_qdrant_client()

    semantic_model = load_semantic_model()
    vector_size = semantic_model.get_sentence_embedding_dimension()

    collection_name = create_qdrant_collection(qdrant_client, vector_size)

    unprocessed_chunks = get_unchunked_from_qdrant(qdrant_client, conn)

    if not unprocessed_chunks:
        log_event(conn, None, "INFO", "No chunks to embed (all already processed)")
        conn.close()
        return {"processed": 0, "errors": 0}

    document_cache = {}
    batch_size = 32

    total_success = 0
    total_errors = 0

    for i in range(0, len(unprocessed_chunks), batch_size):
        batch = unprocessed_chunks[i : i + batch_size]
        success, errors = process_chunk_batch(
            qdrant_client, collection_name, semantic_model, batch, document_cache, conn
        )
        total_success += success
        total_errors += errors

    summary_message = (
        f"Embedding completed: {total_success} chunks embedded, {total_errors} errors"
    )
    log_event(conn, None, "INFO", summary_message)

    conn.close()

    return {"processed": total_success, "errors": total_errors}


if __name__ == "__main__":
    results = run_embedding()
    print(f"Processed: {results['processed']}")
    print(f"Errors: {results['errors']}")
