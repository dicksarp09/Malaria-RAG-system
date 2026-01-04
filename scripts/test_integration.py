"""
Integration tests for the RAG system
Tests the full query flow from API to LLM
"""

import pytest
import requests
import time

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def server():
    """Start and stop the backend server"""
    import subprocess
    import sys
    from pathlib import Path

    # Start server
    backend_dir = Path(__file__).parent.parent / "backend"
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(10)

    yield

    # Cleanup
    server_process.terminate()
    server_process.wait(timeout=5)


def test_health_check(server):
    """Test that server is running"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_query_basic(server):
    """Test a basic RAG query"""
    payload = {"user_query": "What is malaria?", "country": None, "top_k": 5}

    response = requests.post(f"{BASE_URL}/query", json=payload, timeout=30)

    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "retrieved_chunks" in data
    assert "chunks_retrieved" in data


def test_query_with_country_filter(server):
    """Test query with country filter"""
    payload = {"user_query": "malaria diagnosis", "country": "Ghana", "top_k": 3}

    response = requests.post(f"{BASE_URL}/query", json=payload, timeout=30)

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "malaria diagnosis"
    assert isinstance(data["chunks_retrieved"], int)


def test_query_insufficient_evidence(server):
    """Test query that might return insufficient evidence"""
    payload = {
        "user_query": "quantum computing in malaria research",
        "country": None,
        "top_k": 5,
    }

    response = requests.post(f"{BASE_URL}/query", json=payload, timeout=30)

    assert response.status_code == 200
    data = response.json()
    # Should have is_insufficient_evidence field
    assert "is_insufficient_evidence" in data


def test_query_top_k_parameter(server):
    """Test different top_k values"""
    for top_k in [3, 5, 10]:
        payload = {"user_query": "malaria treatment", "country": None, "top_k": top_k}

        response = requests.post(f"{BASE_URL}/query", json=payload, timeout=30)

        assert response.status_code == 200
        data = response.json()
        assert data["chunks_retrieved"] <= top_k


def test_response_time(server):
    """Test that queries complete within reasonable time"""
    payload = {"user_query": "malaria symptoms", "country": "Nigeria", "top_k": 5}

    start_time = time.time()
    response = requests.post(f"{BASE_URL}/query", json=payload, timeout=60)
    elapsed_time = time.time() - start_time

    assert response.status_code == 200
    assert elapsed_time < 30, f"Query took too long: {elapsed_time}s"
