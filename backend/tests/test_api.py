"""
Unit tests for backend API
"""

import pytest
from pathlib import Path


def test_main_file_exists():
    """Test that main.py exists in backend directory"""
    # tests/ is a subdirectory of backend/, so we need parent.parent
    backend_dir = Path(__file__).parent.parent
    main_file = backend_dir / "main.py"
    assert main_file.exists()


def test_qdrant_client_exists():
    """Test Qdrant client can be imported"""
    try:
        from qdrant_client import QdrantClient

        assert QdrantClient is not None
    except ImportError:
        pytest.skip("Qdrant client not installed")


def test_groq_client_exists():
    """Test Groq client can be imported"""
    try:
        from groq import Groq

        assert Groq is not None
    except ImportError:
        pytest.skip("Groq client not installed")


def test_fastapi_exists():
    """Test FastAPI can be imported"""
    try:
        from fastapi import FastAPI

        assert FastAPI is not None
    except ImportError:
        pytest.skip("FastAPI not installed")


def test_langsmith_imports():
    """Test LangSmith can be imported"""
    try:
        from langsmith import Client

        assert Client is not None
    except ImportError:
        pytest.skip("LangSmith not installed")


def test_langsmith_v3_exists():
    """Test LangSmith v3 tracer can be imported"""
    import sys

    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    try:
        from simple_langsmith_v3 import log_query, LANGSMITH_ENABLED

        assert callable(log_query)
        assert isinstance(LANGSMITH_ENABLED, bool)
    except ImportError as e:
        pytest.fail(f"Failed to import simple_langsmith_v3: {e}")
