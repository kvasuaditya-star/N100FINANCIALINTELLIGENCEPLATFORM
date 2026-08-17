from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_screener_valid():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    for item in data:
        assert item["return_on_equity_pct"] >= 15


def test_screener_invalid_de():
    response = client.get("/api/v1/screener?max_de=-1")
    assert response.status_code == 400
