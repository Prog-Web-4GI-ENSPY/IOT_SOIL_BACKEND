import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User


class TestRegister:
    """Tests pour l'endpoint d'inscription"""

    def test_register_success(self, client: TestClient, db: Session):
        """Test d'inscription réussie"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "nom": "Nouveau",
                "prenom": "User",
                "email": "newuser@example.com",
                "telephone": "0123456789",
                "password": "NewPassword123",
                "role": "user"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["nom"] == "Nouveau"
        assert data["prenom"] == "User"
        assert "id" in data
        assert "password" not in data

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test d'inscription avec email existant"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "nom": "Test",
                "prenom": "User",
                "email": test_user.email,
                "password": "Password123",
                "role": "user"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_password(self, client: TestClient):
        """Test d'inscription avec mot de passe invalide"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "nom": "Test",
                "prenom": "User",
                "email": "test@example.com",
                "password": "weak",
                "role": "user"
            }
        )

        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Test d'inscription avec email invalide"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "nom": "Test",
                "prenom": "User",
                "email": "invalid-email",
                "password": "Password123",
                "role": "user"
            }
        )

        assert response.status_code == 422


class TestLogin:
    """Tests pour l'endpoint de connexion"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test de connexion réussie"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test de connexion avec mauvais mot de passe"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_wrong_email(self, client: TestClient):
        """Test de connexion avec mauvais email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "TestPassword123"
            }
        )

        assert response.status_code == 401

    def test_login_invalid_format(self, client: TestClient):
        """Test de connexion avec format invalide"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "invalid-email",
                "password": "test"
            }
        )

        assert response.status_code == 422


class TestRefreshToken:
    """Tests pour l'endpoint de rafraîchissement de token"""

    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test de rafraîchissement réussi"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """Test de rafraîchissement avec token invalide"""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401

    def test_refresh_token_with_access_token(self, client: TestClient, test_user: User):
        """Test de rafraîchissement avec token d'accès au lieu de refresh"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123"
            }
        )
        access_token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )

        assert response.status_code == 401


class TestLogout:
    """Tests pour l'endpoint de déconnexion"""

    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """Test de déconnexion réussie"""
        response = client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )

        assert response.status_code == 204

    def test_logout_without_token(self, client: TestClient):
        """Test de déconnexion sans token"""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 403


class TestGetCurrentUser:
    """Tests pour l'endpoint de récupération de l'utilisateur actuel"""

    def test_get_current_user_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test de récupération de l'utilisateur actuel"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["nom"] == test_user.nom
        assert data["id"] == str(test_user.id)

    def test_get_current_user_without_token(self, client: TestClient):
        """Test de récupération sans token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test de récupération avec token invalide"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token"}
        )

        assert response.status_code == 401


class TestChangePassword:
    """Tests pour l'endpoint de changement de mot de passe"""

    def test_change_password_success(self, client: TestClient, auth_headers: dict):
        """Test de changement de mot de passe réussi"""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "TestPassword123",
                "new_password": "NewPassword456"
            }
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "NewPassword456"
            }
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_old_password(self, client: TestClient, auth_headers: dict):
        """Test de changement avec mauvais ancien mot de passe"""
        response = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "WrongOldPassword",
                "new_password": "NewPassword456"
            }
        )

        assert response.status_code == 400

    def test_change_password_without_token(self, client: TestClient):
        """Test de changement sans token"""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "TestPassword123",
                "new_password": "NewPassword456"
            }
        )

        assert response.status_code == 403


class TestVerifyToken:
    """Tests pour l'endpoint de vérification de token"""

    def test_verify_token_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test de vérification de token valide"""
        response = client.post(
            "/api/v1/auth/verify-token",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role.value

    def test_verify_token_invalid(self, client: TestClient):
        """Test de vérification de token invalide"""
        response = client.post(
            "/api/v1/auth/verify-token",
            headers={"Authorization": "Bearer invalid.token"}
        )

        assert response.status_code == 401

    def test_verify_token_without_token(self, client: TestClient):
        """Test de vérification sans token"""
        response = client.post("/api/v1/auth/verify-token")

        assert response.status_code == 403


class TestValidateToken:
    """Tests pour l'endpoint de validation de token"""

    def test_validate_token_success(self, client: TestClient, user_token: str, test_user: User):
        """Test de validation de token valide"""
        response = client.post(
            "/api/v1/auth/validate-token",
            json={"token": user_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user_id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role.value
        assert data["expires_at"] is not None
        assert data["issued_at"] is not None

    def test_validate_token_invalid(self, client: TestClient):
        """Test de validation de token invalide"""
        response = client.post(
            "/api/v1/auth/validate-token",
            json={"token": "invalid.token.here"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["user_id"] is None

    def test_validate_refresh_token_as_access(self, client: TestClient, test_user: User):
        """Test de validation d'un refresh token comme access token"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/validate-token",
            json={"token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
