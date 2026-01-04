import sqlite3
import os
from pathlib import Path


def get_db_path():
    return Path(__file__).parent.parent / "data" / "metadata" / "documents.db"


def create_database():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            checksum TEXT UNIQUE NOT NULL,
            disease TEXT DEFAULT NULL,
            disease_confidence REAL DEFAULT NULL,
            country TEXT DEFAULT NULL,
            country_confidence REAL DEFAULT NULL,
            language TEXT DEFAULT NULL,
            ingestion_status TEXT NOT NULL DEFAULT 'pending',
            rejection_reason TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT DEFAULT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        )
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_checksum ON documents(checksum)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(ingestion_status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_logs_document ON ingestion_logs(document_id)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON ingestion_logs(level)")

    conn.commit()
    conn.close()

    return db_path


if __name__ == "__main__":
    db_path = create_database()
    print(f"Database created at: {db_path}")
