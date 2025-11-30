import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    """Test d'inscription d'un utilisateur"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nom": "Nouveau",
            "prenom": "User",
            "email": "nouveau@example.com",
            "telephone": "+237612345670",
            "password": "Test1234!",
            "role": "user"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nouveau@example.com"
    assert "password" not in data


def test_register_duplicate_email(client: TestClient, test_user):
    """Test d'inscription avec email existant"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nom": "Test",
            "prenom": "Duplicate",
            "email": test_user.email,
            "telephone": "+237612345671",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


def test_login_success(client: TestClient, test_user):
    """Test de connexion réussie"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == "test@example.com"


def test_login_wrong_password(client: TestClient, test_user):
    """Test de connexion avec mauvais mot de passe"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test de connexion avec utilisateur inexistant"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Test1234!"
        }
    )
    
    assert response.status_code == 401


def test_get_current_user(client: TestClient, auth_headers):
    """Test de récupération de l'utilisateur courant"""
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_get_current_user_no_token(client: TestClient):
    """Test sans token d'authentification"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
