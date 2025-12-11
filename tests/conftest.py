import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import get_db
from app.models.base import Base
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
from main import app
from datetime import datetime

# Base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """Créer une base de données de test pour chaque test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """Client de test FastAPI"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db) -> User:
    """Créer un utilisateur de test"""
    from app.services.auth_service import auth_service

    user = User(
        nom="Test",
        prenom="User",
        email="test@example.com",
        telephone="+237612345678",
        password_hash=auth_service.get_password_hash("TestPassword123"),
        role=UserRole.USER,
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db) -> User:
    """Créer un admin de test"""
    from app.services.auth_service import auth_service

    admin = User(
        nom="Admin",
        prenom="User",
        email="admin@example.com",
        telephone="+237612345679",
        password_hash=auth_service.get_password_hash("AdminPassword123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_inactive_user(db) -> User:
    """Créer un utilisateur inactif de test"""
    from app.services.auth_service import auth_service

    user = User(
        nom="Inactive",
        prenom="User",
        email="inactive@example.com",
        telephone="+237612345680",
        password_hash=auth_service.get_password_hash("InactivePassword123"),
        role=UserRole.USER,
        status=UserStatus.INACTIVE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Headers d'authentification pour les tests"""
    from app.core.security import create_access_token
    access_token = create_access_token(
        data={"sub": test_user.id, "email": test_user.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(test_admin) -> dict:
    """Headers admin pour les tests"""
    from app.core.security import create_access_token
    access_token = create_access_token(
        data={"sub": test_admin.id, "email": test_admin.email}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def user_token(test_user) -> str:
    """Token d'accès pour l'utilisateur de test"""
    from app.core.security import create_access_token
    return create_access_token(
        data={"sub": test_user.id, "email": test_user.email}
    )
