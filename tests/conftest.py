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
    from app.services.auth import auth_service
    
    user = User(
        nom="Test",
        prenom="User",
        email="test@example.com",
        telephone="+237612345678",
        password_hash=auth_service.get_password_hash("Test1234!"),
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
    from app.services.auth import auth_service
    
    admin = User(
        nom="Admin",
        prenom="User",
        email="admin@example.com",
        telephone="+237612345679",
        password_hash=auth_service.get_password_hash("Admin1234!"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Headers d'authentification pour les tests"""
    access_token = create_access_token(
        data={"sub": test_user.email, "user_id": test_user.id}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(test_admin) -> dict:
    """Headers admin pour les tests"""
    access_token = create_access_token(
        data={"sub": test_admin.email, "user_id": test_admin.id}
    )
    return {"Authorization": f"Bearer {access_token}"}
