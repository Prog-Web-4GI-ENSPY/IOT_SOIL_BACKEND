import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.users_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserPreferences
from app.models.user import User, UserRole, UserStatus


class TestUserServiceGetters:
    """Tests pour les méthodes de récupération du service utilisateur"""

    def test_get_user_by_id_success(self, db: Session, test_user: User):
        """Test de récupération d'un utilisateur par ID"""
        user = UserService.get_user_by_id(db, str(test_user.id))

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_user_by_id_not_found(self, db: Session):
        """Test de récupération d'un utilisateur inexistant"""
        user = UserService.get_user_by_id(db, "nonexistent-id")
        assert user is None

    def test_get_user_by_email_success(self, db: Session, test_user: User):
        """Test de récupération d'un utilisateur par email"""
        user = UserService.get_user_by_email(db, test_user.email)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_user_by_email_not_found(self, db: Session):
        """Test de récupération d'un utilisateur inexistant par email"""
        user = UserService.get_user_by_email(db, "nonexistent@example.com")
        assert user is None


class TestUserServiceCreate:
    """Tests pour la création d'utilisateurs"""

    def test_create_user_success(self, db: Session):
        """Test de création d'un utilisateur"""
        user_data = UserCreate(
            nom="Nouveau",
            prenom="Utilisateur",
            email="nouveau@example.com",
            telephone="0123456789",
            password="NewPassword123",
            role=UserRole.USER
        )

        user = UserService.create_user(db, user_data)

        assert user.id is not None
        assert user.nom == "Nouveau"
        assert user.prenom == "Utilisateur"
        assert user.email == "nouveau@example.com"
        assert user.telephone == "0123456789"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        assert user.password_hash != "NewPassword123"

    def test_create_user_with_preferences(self, db: Session):
        """Test de création d'un utilisateur avec préférences"""
        preferences = UserPreferences(
            langue="en",
            theme="dark"
        )
        user_data = UserCreate(
            nom="Nouveau",
            prenom="Utilisateur",
            email="nouveau2@example.com",
            password="NewPassword123",
            role=UserRole.USER,
            preferences=preferences
        )

        user = UserService.create_user(db, user_data)

        assert user.preferences is not None
        assert user.preferences["langue"] == "en"
        assert user.preferences["theme"] == "dark"

    def test_create_user_duplicate_email(self, db: Session, test_user: User):
        """Test de création d'un utilisateur avec email existant"""
        user_data = UserCreate(
            nom="Duplicate",
            prenom="User",
            email=test_user.email,
            password="Password123",
            role=UserRole.USER
        )

        with pytest.raises(HTTPException) as exc_info:
            UserService.create_user(db, user_data)

        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()


class TestUserServiceUpdate:
    """Tests pour la mise à jour d'utilisateurs"""

    def test_update_user_success(self, db: Session, test_user: User):
        """Test de mise à jour d'un utilisateur"""
        update_data = UserUpdate(
            nom="Updated",
            prenom="Name"
        )

        updated_user = UserService.update_user(db, str(test_user.id), update_data)

        assert updated_user.nom == "Updated"
        assert updated_user.prenom == "Name"
        assert updated_user.email == test_user.email

    def test_update_user_partial(self, db: Session, test_user: User):
        """Test de mise à jour partielle d'un utilisateur"""
        update_data = UserUpdate(nom="OnlyName")

        updated_user = UserService.update_user(db, str(test_user.id), update_data)

        assert updated_user.nom == "OnlyName"
        assert updated_user.prenom == test_user.prenom

    def test_update_user_not_found(self, db: Session):
        """Test de mise à jour d'un utilisateur inexistant"""
        update_data = UserUpdate(nom="Test")

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_user(db, "nonexistent-id", update_data)

        assert exc_info.value.status_code == 404


class TestUserServiceDelete:
    """Tests pour la suppression d'utilisateurs"""

    def test_delete_user_success(self, db: Session, test_user: User):
        """Test de suppression d'un utilisateur"""
        user_id = str(test_user.id)
        result = UserService.delete_user(db, user_id)

        assert result is True
        assert UserService.get_user_by_id(db, user_id) is None

    def test_delete_user_not_found(self, db: Session):
        """Test de suppression d'un utilisateur inexistant"""
        with pytest.raises(HTTPException) as exc_info:
            UserService.delete_user(db, "nonexistent-id")

        assert exc_info.value.status_code == 404


class TestUserServiceAuthentication:
    """Tests pour l'authentification"""

    def test_authenticate_user_success(self, db: Session, test_user: User):
        """Test d'authentification réussie"""
        user = UserService.authenticate_user(
            db,
            "test@example.com",
            "TestPassword123"
        )

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_authenticate_user_wrong_password(self, db: Session, test_user: User):
        """Test d'authentification avec mauvais mot de passe"""
        user = UserService.authenticate_user(
            db,
            "test@example.com",
            "WrongPassword"
        )

        assert user is None

    def test_authenticate_user_wrong_email(self, db: Session):
        """Test d'authentification avec mauvais email"""
        user = UserService.authenticate_user(
            db,
            "wrong@example.com",
            "TestPassword123"
        )

        assert user is None


class TestUserServicePasswordChange:
    """Tests pour le changement de mot de passe"""

    def test_change_password_success(self, db: Session, test_user: User):
        """Test de changement de mot de passe réussi"""
        old_hash = test_user.password_hash

        updated_user = UserService.change_password(
            db,
            test_user,
            "TestPassword123",
            "NewPassword123"
        )

        assert updated_user.password_hash != old_hash

        authenticated = UserService.authenticate_user(
            db,
            test_user.email,
            "NewPassword123"
        )
        assert authenticated is not None

    def test_change_password_wrong_old_password(self, db: Session, test_user: User):
        """Test de changement de mot de passe avec mauvais ancien mot de passe"""
        with pytest.raises(HTTPException) as exc_info:
            UserService.change_password(
                db,
                test_user,
                "WrongOldPassword",
                "NewPassword123"
            )

        assert exc_info.value.status_code == 400
        assert "incorrect password" in exc_info.value.detail.lower()


class TestUserServiceStatus:
    """Tests pour la gestion du statut"""

    def test_change_user_status_success(self, db: Session, test_user: User):
        """Test de changement de statut réussi"""
        updated_user = UserService.change_user_status(
            db,
            str(test_user.id),
            UserStatus.SUSPENDED
        )

        assert updated_user.status == UserStatus.SUSPENDED

    def test_change_user_status_not_found(self, db: Session):
        """Test de changement de statut d'un utilisateur inexistant"""
        with pytest.raises(HTTPException) as exc_info:
            UserService.change_user_status(
                db,
                "nonexistent-id",
                UserStatus.SUSPENDED
            )

        assert exc_info.value.status_code == 404

    def test_update_last_access(self, db: Session, test_user: User):
        """Test de mise à jour du dernier accès"""
        old_access = test_user.dernier_acces

        updated_user = UserService.update_last_access(db, test_user)

        assert updated_user.dernier_acces is not None
        assert updated_user.dernier_acces != old_access


class TestUserServiceGetAll:
    """Tests pour la récupération de tous les utilisateurs"""

    def test_get_all_users(self, db: Session, test_user: User, test_admin: User):
        """Test de récupération de tous les utilisateurs"""
        users = UserService.get_all_users(db)

        assert len(users) >= 2
        user_emails = [u.email for u in users]
        assert test_user.email in user_emails
        assert test_admin.email in user_emails

    def test_get_all_users_with_pagination(self, db: Session, test_user: User, test_admin: User):
        """Test de récupération avec pagination"""
        users = UserService.get_all_users(db, skip=0, limit=1)

        assert len(users) == 1

    def test_get_all_users_filter_by_status(self, db: Session, test_user: User, test_inactive_user: User):
        """Test de récupération avec filtre par statut"""
        active_users = UserService.get_all_users(db, status=UserStatus.ACTIVE)
        inactive_users = UserService.get_all_users(db, status=UserStatus.INACTIVE)

        assert test_user in active_users
        assert test_inactive_user not in active_users
        assert test_inactive_user in inactive_users

    def test_get_all_users_filter_by_role(self, db: Session, test_user: User, test_admin: User):
        """Test de récupération avec filtre par rôle"""
        admins = UserService.get_all_users(db, role=UserRole.ADMIN)
        users = UserService.get_all_users(db, role=UserRole.USER)

        assert test_admin in admins
        assert test_user not in admins
        assert test_user in users
