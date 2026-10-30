from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@campusops.edu",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"
    assert data["user"]["email"] == "admin@campusops.edu"

def test_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "email": "admin@campusops.edu",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_auth_me_with_token():
    # Login first
    login_res = client.post("/api/v1/auth/login", json={
        "email": "faculty@campusops.edu",
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "faculty"

