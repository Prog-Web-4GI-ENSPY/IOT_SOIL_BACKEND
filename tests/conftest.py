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
def db() -> Generator[Session, None, None]:
    """
    Fixture pour créer une session de base de données de test
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Fixture pour créer un client de test FastAPI
    """
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
def test_user(db: Session) -> User:
    """
    Fixture pour créer un utilisateur de test
    """
    user = User(
        nom="Test",
        prenom="User",
        email="test@example.com",
        telephone="0123456789",
        password_hash=get_password_hash("TestPassword123"),
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        date_inscription=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db: Session) -> User:
    """
    Fixture pour créer un administrateur de test
    """
    admin = User(
        nom="Admin",
        prenom="User",
        email="admin@example.com",
        telephone="0987654321",
        password_hash=get_password_hash("AdminPassword123"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        date_inscription=datetime.utcnow()
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_inactive_user(db: Session) -> User:
    """
    Fixture pour créer un utilisateur inactif de test
    """
    user = User(
        nom="Inactive",
        prenom="User",
        email="inactive@example.com",
        telephone="1122334455",
        password_hash=get_password_hash("InactivePassword123"),
        role=UserRole.USER,
        status=UserStatus.INACTIVE,
        date_inscription=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_token(client: TestClient, test_user: User) -> str:
    """
    Fixture pour obtenir un token d'accès pour l'utilisateur de test
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client: TestClient, test_admin: User) -> str:
    """
    Fixture pour obtenir un token d'accès pour l'admin de test
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """
    Fixture pour créer les headers d'authentification pour l'utilisateur
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """
    Fixture pour créer les headers d'authentification pour l'admin
    """
    return {"Authorization": f"Bearer {admin_token}"}
