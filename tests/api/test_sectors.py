from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10


def test_get_sector_companies():
    response = client.get("/api/v1/sectors/Energy/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["broad_sector"] == "Energy"
