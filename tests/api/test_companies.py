from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_companies_list():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92
    assert data[0]["id"] is not None


def test_get_company_profile():
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["id"] == "TCS"
    assert "Tata Consultancy Services" in data["profile"]["company_name"]


def test_get_company_not_found():
    response = client.get("/api/v1/companies/INVALID")
    assert response.status_code == 404
