from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check():
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "documents_indexed" in data


def test_query_without_engine():
    """Test the /query endpoint when the engine is not initialized."""
    # TestClient doesn't automatically trigger lifespan events unless used as context manager.
    # So query_engine is None. We expect a 503.
    response = client.post("/query", json={"question": "Test question", "top_k": 3})
    assert response.status_code == 503
    assert "Query engine is not initialized" in response.json()["detail"]
