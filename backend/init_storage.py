#!/usr/bin/env python3
"""Initialize database and Qdrant storage for Render deployment."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def init_database():
    """Initialize SQLite database."""
    from scripts.create_db import create_database

    db_path = create_database()
    print(f"✓ Database initialized at {db_path}")
    return db_path


def init_qdrant():
    """Initialize Qdrant collection."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance

    client = QdrantClient(path=str(Path(__file__).parent.parent / "data" / "qdrant_collection"))

    collection_name = "malaria_chunks"

    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if not exists:
        # Create collection with sentence-transformers dimensions (384 for all-MiniLM-L6-v2)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"✓ Created Qdrant collection: {collection_name}")
    else:
        print(f"✓ Qdrant collection exists: {collection_name}")

    return collection_name


if __name__ == "__main__":
    print("Initializing backend storage...")
    try:
        init_database()
        init_qdrant()
        print("\n✓ Initialization complete!")
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        sys.exit(1)
