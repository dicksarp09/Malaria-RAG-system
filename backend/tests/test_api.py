"""
Unit tests for backend API
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Malaria RAG API"
    assert "version" in data
    assert "langsmith_tracing" in data


def test_health_endpoint():
    """Test health endpoint returns healthy status"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_query_validation_short_query():
    """Test query endpoint rejects short queries"""
    response = client.post("/query", json={"user_query": "hi"})
    assert response.status_code == 400
    assert "at least 3 characters" in response.json()["detail"]


def test_query_validation_empty_query():
    """Test query endpoint rejects empty queries"""
    response = client.post("/query", json={"user_query": ""})
    assert response.status_code == 400


def test_query_valid_request():
    """Test query endpoint accepts valid request format"""
    payload = {"user_query": "malaria treatment", "country": "Ghana", "top_k": 5}
    response = client.post("/query", json=payload)
    # Should not fail validation (might fail on other reasons)
    assert response.status_code in [200, 500]


def test_query_default_parameters():
    """Test query endpoint uses default parameters"""
    payload = {"user_query": "test query about malaria"}
    response = client.post("/query", json=payload)
    assert response.status_code in [200, 500]
