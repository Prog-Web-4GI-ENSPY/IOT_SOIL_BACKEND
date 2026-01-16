from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import verify_token
from app.schemas.auth import TokenData

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Récupère l'utilisateur actuellement authentifié

    Args:
        credentials: Credentials d'autorisation HTTP
        db: Session de base de données

    Returns:
        User: L'utilisateur authentifié

    Raises:
        HTTPException: Si le token est invalide ou l'utilisateur n'existe pas
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token, token_type="access")

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Récupère l'utilisateur actuellement authentifié (Simplifié)
    """
    return current_user


def require_role(required_role: UserRole):
    """
    Factory pour créer une dépendance qui vérifie le rôle de l'utilisateur

    Args:
        required_role: Le rôle requis

    Returns:
        Fonction de dépendance qui vérifie le rôle
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User must have {required_role} role"
            )
        return current_user
    return role_checker


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Vérifie que l'utilisateur actuel est un admin

    Args:
        current_user: L'utilisateur actuel

    Returns:
        User: L'utilisateur admin

    Raises:
        HTTPException: Si l'utilisateur n'est pas admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Récupère l'utilisateur actuellement authentifié si un token est fourni

    Args:
        credentials: Credentials d'autorisation HTTP (optionnels)
        db: Session de base de données

    Returns:
        Optional[User]: L'utilisateur authentifié ou None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")

        if payload is None:
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None
