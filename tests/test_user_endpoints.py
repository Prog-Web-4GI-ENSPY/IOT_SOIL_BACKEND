import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserStatus


class TestGetMyProfile:
    """Tests pour l'endpoint de récupération du profil"""

    def test_get_my_profile_success(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test de récupération du profil de l'utilisateur connecté"""
        response = client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["nom"] == test_user.nom
        assert data["id"] == str(test_user.id)

    def test_get_my_profile_without_token(self, client: TestClient):
        """Test de récupération sans token"""
        response = client.get("/api/v1/users/me")

        assert response.status_code == 403


class TestUpdateMyProfile:
    """Tests pour l'endpoint de mise à jour du profil"""

    def test_update_my_profile_success(self, client: TestClient, auth_headers: dict):
        """Test de mise à jour du profil"""
        response = client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "nom": "Updated",
                "prenom": "Name"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nom"] == "Updated"
        assert data["prenom"] == "Name"

    def test_update_my_profile_partial(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test de mise à jour partielle du profil"""
        response = client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"nom": "OnlyName"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nom"] == "OnlyName"
        assert data["prenom"] == test_user.prenom

    def test_update_my_profile_without_token(self, client: TestClient):
        """Test de mise à jour sans token"""
        response = client.put(
            "/api/v1/users/me",
            json={"nom": "Test"}
        )

        assert response.status_code == 403


class TestGetAllUsers:
    """Tests pour l'endpoint de récupération de tous les utilisateurs"""

    def test_get_all_users_as_admin(self, client: TestClient, test_user: User, test_admin: User, admin_headers: dict):
        """Test de récupération de tous les utilisateurs en tant qu'admin"""
        response = client.get(
            "/api/v1/users/",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

        emails = [user["email"] for user in data]
        assert test_user.email in emails
        assert test_admin.email in emails

    def test_get_all_users_as_regular_user(self, client: TestClient, auth_headers: dict):
        """Test de récupération en tant qu'utilisateur normal (doit échouer)"""
        response = client.get(
            "/api/v1/users/",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_get_all_users_with_pagination(self, client: TestClient, admin_headers: dict):
        """Test de récupération avec pagination"""
        response = client.get(
            "/api/v1/users/?skip=0&limit=1",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_all_users_filter_by_status(self, client: TestClient, test_inactive_user: User, admin_headers: dict):
        """Test de récupération avec filtre par statut"""
        response = client.get(
            "/api/v1/users/?status=active",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        inactive_emails = [user["email"] for user in data]
        assert test_inactive_user.email not in inactive_emails

    def test_get_all_users_filter_by_role(self, client: TestClient, admin_headers: dict):
        """Test de récupération avec filtre par rôle"""
        response = client.get(
            "/api/v1/users/?role=admin",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        for user in data:
            assert user["role"] == "admin"

    def test_get_all_users_without_token(self, client: TestClient):
        """Test de récupération sans token"""
        response = client.get("/api/v1/users/")

        assert response.status_code == 403


class TestGetUserById:
    """Tests pour l'endpoint de récupération d'un utilisateur par ID"""

    def test_get_user_by_id_as_admin(self, client: TestClient, test_user: User, admin_headers: dict):
        """Test de récupération par ID en tant qu'admin"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == str(test_user.id)

    def test_get_user_by_id_as_regular_user(self, client: TestClient, test_user: User, auth_headers: dict):
        """Test de récupération par ID en tant qu'utilisateur normal (doit échouer)"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_get_user_by_id_not_found(self, client: TestClient, admin_headers: dict):
        """Test de récupération d'un utilisateur inexistant"""
        response = client.get(
            "/api/v1/users/nonexistent-id",
            headers=admin_headers
        )

        assert response.status_code == 404


class TestUpdateUser:
    """Tests pour l'endpoint de mise à jour d'un utilisateur"""

    def test_update_user_as_admin(self, client: TestClient, test_user: User, admin_headers: dict):
        """Test de mise à jour en tant qu'admin"""
        response = client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
            json={
                "nom": "UpdatedByAdmin",
                "prenom": "User"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nom"] == "UpdatedByAdmin"

    def test_update_user_as_regular_user(self, client: TestClient, test_admin: User, auth_headers: dict):
        """Test de mise à jour en tant qu'utilisateur normal (doit échouer)"""
        response = client.put(
            f"/api/v1/users/{test_admin.id}",
            headers=auth_headers,
            json={"nom": "Test"}
        )

        assert response.status_code == 403


class TestDeleteUser:
    """Tests pour l'endpoint de suppression d'un utilisateur"""

    def test_delete_user_as_admin(self, client: TestClient, test_user: User, admin_headers: dict):
        """Test de suppression en tant qu'admin"""
        response = client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )

        assert response.status_code == 204

        get_response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404

    def test_delete_user_as_regular_user(self, client: TestClient, test_admin: User, auth_headers: dict):
        """Test de suppression en tant qu'utilisateur normal (doit échouer)"""
        response = client.delete(
            f"/api/v1/users/{test_admin.id}",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_delete_self(self, client: TestClient, test_admin: User, admin_headers: dict):
        """Test de suppression de son propre compte (doit échouer)"""
        response = client.delete(
            f"/api/v1/users/{test_admin.id}",
            headers=admin_headers
        )

        assert response.status_code == 400
        assert "cannot delete your own account" in response.json()["detail"].lower()


class TestChangeUserStatus:
    """Tests pour l'endpoint de changement de statut"""

    def test_change_user_status_as_admin(self, client: TestClient, test_user: User, admin_headers: dict):
        """Test de changement de statut en tant qu'admin"""
        response = client.patch(
            f"/api/v1/users/{test_user.id}/status?new_status=suspended",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "suspended"

    def test_change_user_status_as_regular_user(self, client: TestClient, test_admin: User, auth_headers: dict):
        """Test de changement de statut en tant qu'utilisateur normal (doit échouer)"""
        response = client.patch(
            f"/api/v1/users/{test_admin.id}/status?new_status=suspended",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_change_own_status(self, client: TestClient, test_admin: User, admin_headers: dict):
        """Test de changement de son propre statut (doit échouer)"""
        response = client.patch(
            f"/api/v1/users/{test_admin.id}/status?new_status=suspended",
            headers=admin_headers
        )

        assert response.status_code == 400


class TestActivateUser:
    """Tests pour l'endpoint d'activation d'utilisateur"""

    def test_activate_user_as_admin(self, client: TestClient, test_inactive_user: User, admin_headers: dict):
        """Test d'activation en tant qu'admin"""
        response = client.patch(
            f"/api/v1/users/{test_inactive_user.id}/activate",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_activate_user_as_regular_user(self, client: TestClient, test_inactive_user: User, auth_headers: dict):
        """Test d'activation en tant qu'utilisateur normal (doit échouer)"""
        response = client.patch(
            f"/api/v1/users/{test_inactive_user.id}/activate",
            headers=auth_headers
        )

        assert response.status_code == 403


class TestSuspendUser:
    """Tests pour l'endpoint de suspension d'utilisateur"""

    def test_suspend_user_as_admin(self, client: TestClient, test_user: User, admin_headers: dict):
        """Test de suspension en tant qu'admin"""
        response = client.patch(
            f"/api/v1/users/{test_user.id}/suspend",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "suspended"

    def test_suspend_user_as_regular_user(self, client: TestClient, test_admin: User, auth_headers: dict):
        """Test de suspension en tant qu'utilisateur normal (doit échouer)"""
        response = client.patch(
            f"/api/v1/users/{test_admin.id}/suspend",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_suspend_self(self, client: TestClient, test_admin: User, admin_headers: dict):
        """Test de suspension de son propre compte (doit échouer)"""
        response = client.patch(
            f"/api/v1/users/{test_admin.id}/suspend",
            headers=admin_headers
        )

        assert response.status_code == 400
        assert "cannot suspend your own account" in response.json()["detail"].lower()

    def test_suspended_user_cannot_access(self, client: TestClient, test_user: User, db: Session):
        """Test qu'un utilisateur suspendu ne peut pas accéder à l'API"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123"
            }
        )
        token = login_response.json()["access_token"]

        from app.services.users_service import UserService
        UserService.change_user_status(db, str(test_user.id), UserStatus.SUSPENDED)

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "suspended" in response.json()["detail"].lower()
