import sqlite3
import hashlib
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


def compute_checksum(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def log_event(conn, document_id: str, level: str, message: str):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ingestion_logs (document_id, level, message) VALUES (?, ?, ?)",
        (document_id, level, message),
    )
    conn.commit()


def document_exists(conn, checksum: str) -> tuple[bool, str | None]:
    cursor = conn.cursor()
    cursor.execute("SELECT document_id FROM documents WHERE checksum = ?", (checksum,))
    row = cursor.fetchone()
    if row:
        return True, row[0]
    return False, None


def insert_document(
    conn, document_id: str, filename: str, file_path: str, checksum: str
):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO documents (document_id, filename, file_path, checksum, ingestion_status)
        VALUES (?, ?, ?, ?, 'pending')
        """,
        (document_id, filename, file_path, checksum),
    )
    conn.commit()


def ingest_pdfs():
    db_path = get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run create_db.py first."
        )

    pdfs_dir = get_pdfs_dir()
    if not pdfs_dir.exists():
        raise FileNotFoundError(f"PDFs directory not found at {pdfs_dir}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        log_event(conn, None, "INFO", "No PDF files found in directory")
        return

    ingested_count = 0
    skipped_count = 0
    error_count = 0

    for pdf_path in pdf_files:
        try:
            filename = pdf_path.name
            file_path = str(pdf_path)

            try:
                checksum = compute_checksum(file_path)
            except Exception as e:
                error_count += 1
                log_event(
                    conn, None, "ERROR", f"Failed to read file {filename}: {str(e)}"
                )
                continue

            exists, existing_doc_id = document_exists(conn, checksum)

            if exists:
                skipped_count += 1
                log_event(
                    conn,
                    existing_doc_id,
                    "INFO",
                    f"Duplicate file skipped: {filename} (checksum: {checksum})",
                )
                continue

            document_id = str(uuid.uuid4())
            insert_document(conn, document_id, filename, file_path, checksum)
            ingested_count += 1
            log_event(
                conn,
                document_id,
                "INFO",
                f"Document registered: {filename} (checksum: {checksum})",
            )

        except Exception as e:
            error_count += 1
            log_event(
                conn,
                None,
                "ERROR",
                f"Unexpected error processing {pdf_path.name}: {str(e)}",
            )

    log_event(
        conn,
        None,
        "INFO",
        f"Ingestion completed: {ingested_count} new, {skipped_count} duplicates, {error_count} errors",
    )

    conn.close()

    return ingested_count, skipped_count, error_count


if __name__ == "__main__":
    ingested, skipped, errors = ingest_pdfs()
    print(f"New documents: {ingested}")
    print(f"Duplicates skipped: {skipped}")
    print(f"Errors: {errors}")
