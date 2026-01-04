import sqlite3
import fitz
import uuid
from pathlib import Path


def get_db_path():
    return Path(__file__).parent.parent / "data" / "metadata" / "documents.db"


def get_pdfs_dir():
    base_dir = Path(__file__).parent.parent / "data" / "raw"
    pdfs_dir = base_dir / "pfds"
    if not pdfs_dir.exists():
        pdfs_dir = base_dir / "pdfs"
    return pdfs_dir


def log_event(conn, document_id: str, level: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (document_id, level, message) VALUES (?, ?, ?)",
        (document_id, level, message),
    )
    conn.commit()


def create_chunks_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            section TEXT NOT NULL,
            text TEXT NOT NULL,
            char_count INTEGER NOT NULL,
            page_start INTEGER NOT NULL,
            page_end INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section)")
    conn.commit()


def get_unchunked_documents(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.document_id, d.filename, d.file_path 
        FROM documents d 
        WHERE d.ingestion_status = 'accepted' 
        AND NOT EXISTS (
            SELECT 1 FROM chunks c WHERE c.document_id = d.document_id
        )
    """)
    return cursor.fetchall()


def has_chunks(conn, document_id: str) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE document_id = ?", (document_id,))
    return cursor.fetchone()[0] > 0


def chunk_text(text: str, page_start: int, page_end: int) -> list:
    min_size = 1000
    max_size = 1500

    chunks = []
    words = text.split()
    current_chunk = []

    for word in words:
        test_chunk = " ".join(current_chunk + [word])
        if len(test_chunk) <= max_size:
            current_chunk.append(word)
        else:
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= min_size:
                    chunks.append((chunk_text, page_start, page_end))
            current_chunk = [word]

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        if len(chunk_text) >= min_size:
            chunks.append((chunk_text, page_start, page_end))

    return chunks


def process_document(
    conn, document_id: str, filename: str, file_path: str, pdfs_dir: Path
) -> dict:
    result = {"status": "success", "chunks_created": 0, "error": None}

    if has_chunks(conn, document_id):
        log_event(conn, document_id, "INFO", f"Skipped: {filename} already has chunks")
        result["status"] = "skipped"
        return result

    full_path = (
        pdfs_dir / Path(file_path).name
        if not Path(file_path).is_absolute()
        else Path(file_path)
    )

    if not full_path.exists():
        log_event(conn, document_id, "ERROR", f"File not found: {filename}")
        result["status"] = "error"
        result["error"] = "File not found"
        return result

    try:
        doc = fitz.open(str(full_path))
        page_count = len(doc)
        full_text = ""

        for page_num in range(page_count):
            page = doc[page_num]
            full_text += " " + str(page.get_text())

        doc.close()

        chunks = chunk_text(full_text, 1, page_count)

        for chunk, page_start, page_end in chunks:
            chunk_id = str(uuid.uuid4())
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chunks (chunk_id, document_id, section, text, char_count, page_start, page_end)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    document_id,
                    "full_text",
                    chunk,
                    len(chunk),
                    page_start,
                    page_end,
                ),
            )
            conn.commit()
            result["chunks_created"] += 1

        message = f"File: {filename}, Chunks created: {result['chunks_created']}, Pages: {page_count}"
        log_event(conn, document_id, "INFO", message)

    except Exception as e:
        log_event(
            conn, document_id, "ERROR", f"Chunking failed for {filename}: {str(e)}"
        )
        result["status"] = "error"
        result["error"] = str(e)

    return result


def run_chunking():
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run create_db.py first."
        )

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    create_chunks_table(conn)

    unchunked_docs = get_unchunked_documents(conn)

    if not unchunked_docs:
        log_event(
            conn,
            None,
            "INFO",
            "No documents to chunk (all already processed or no accepted documents)",
        )
        return {"processed": 0, "skipped": 0, "total_chunks": 0, "errors": 0}

    pdfs_dir = get_pdfs_dir()

    results = {"processed": 0, "skipped": 0, "total_chunks": 0, "errors": 0}

    for document_id, filename, file_path in unchunked_docs:
        try:
            result = process_document(conn, document_id, filename, file_path, pdfs_dir)

            if result["status"] == "success":
                results["processed"] += 1
                results["total_chunks"] += result["chunks_created"]
            elif result["status"] == "skipped":
                results["skipped"] += 1
            else:
                results["errors"] += 1

        except Exception as e:
            log_event(conn, document_id, "ERROR", f"Processing failed: {str(e)}")
            results["errors"] += 1

    summary_message = (
        f"Chunking completed: "
        f"{results['processed']} processed, "
        f"{results['skipped']} skipped, "
        f"{results['total_chunks']} total chunks, "
        f"{results['errors']} errors"
    )
    log_event(conn, None, "INFO", summary_message)

    conn.close()

    return results


if __name__ == "__main__":
    results = run_chunking()
    print(f"Processed: {results['processed']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Total chunks: {results['total_chunks']}")
    print(f"Errors: {results['errors']}")
