from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    TokenValidationRequest,
    TokenValidationResponse
)
from app.schemas.user import UserCreate, UserResponse
from app.services.users_service import UserService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.config import settings
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Inscription d'un nouvel utilisateur

    Args:
        user_data: Données de l'utilisateur à créer
        db: Session de base de données

    Returns:
        UserResponse: L'utilisateur créé

    Raises:
        HTTPException: Si l'email existe déjà
    """
    return UserService.create_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Connexion d'un utilisateur

    Args:
        login_data: Email et mot de passe
        db: Session de base de données

    Returns:
        TokenResponse: Tokens d'accès et de rafraîchissement

    Raises:
        HTTPException: Si les identifiants sont incorrects
    """
    user = UserService.authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mise à jour du dernier accès
    UserService.update_last_access(db, user)

    # Création des tokens
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Rafraîchit le token d'accès

    Args:
        refresh_data: Token de rafraîchissement
        db: Session de base de données

    Returns:
        TokenResponse: Nouveaux tokens

    Raises:
        HTTPException: Si le token de rafraîchissement est invalide
    """
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = UserService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Création de nouveaux tokens
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Déconnexion de l'utilisateur

    Note: Côté client, supprimez les tokens du stockage local
    Dans une implémentation complète, on pourrait ajouter le token à une blacklist

    Args:
        current_user: L'utilisateur actuel

    Returns:
        Statut 204 No Content
    """
    # Dans une implémentation complète, on ajouterait le token à une blacklist
    # ou on utiliserait Redis pour gérer les tokens révoqués
    return None


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère les informations de l'utilisateur connecté

    Args:
        current_user: L'utilisateur actuel

    Returns:
        UserResponse: Informations de l'utilisateur
    """
    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change le mot de passe de l'utilisateur connecté

    Args:
        password_data: Ancien et nouveau mot de passe
        current_user: L'utilisateur actuel
        db: Session de base de données

    Returns:
        Message de confirmation

    Raises:
        HTTPException: Si l'ancien mot de passe est incorrect
    """
    UserService.change_password(
        db,
        current_user,
        password_data.old_password,
        password_data.new_password
    )

    return {"message": "Password changed successfully"}


@router.post("/verify-token", response_model=TokenValidationResponse)
def verify_token_endpoint(
    current_user: User = Depends(get_current_user)
):
    """
    Vérifie la validité du token d'accès

    Args:
        current_user: L'utilisateur actuel (récupéré via le token)

    Returns:
        TokenValidationResponse: Informations sur la validité du token
    """
    from fastapi import Request
    from fastapi.security import HTTPBearer

    # Cette route vérifie automatiquement le token via la dépendance get_current_user
    # Si on arrive ici, le token est valide

    return TokenValidationResponse(
        valid=True,
        user_id=str(current_user.id),
        email=current_user.email,
        role=current_user.role.value,
        expires_at=None,  # Pourrait être extrait du token si nécessaire
        issued_at=None
    )


@router.post("/validate-token", response_model=TokenValidationResponse)
def validate_token(
    request: TokenValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Valide un token sans utiliser les headers d'authentification

    Args:
        request: La requête contenant le token à valider
        db: Session de base de données

    Returns:
        TokenValidationResponse: Informations sur la validité du token
    """
    payload = verify_token(request.token, token_type="access")

    if payload is None:
        return TokenValidationResponse(
            valid=False,
            user_id=None,
            email=None,
            role=None,
            expires_at=None,
            issued_at=None
        )

    user_id = payload.get("sub")
    user = UserService.get_user_by_id(db, user_id)

    if not user:
        return TokenValidationResponse(
            valid=False,
            user_id=None,
            email=None,
            role=None,
            expires_at=None,
            issued_at=None
        )

    # Convertir les timestamps UNIX en datetime
    expires_at = datetime.fromtimestamp(payload.get("exp")) if payload.get("exp") else None
    issued_at = datetime.fromtimestamp(payload.get("iat")) if payload.get("iat") else None

    return TokenValidationResponse(
        valid=True,
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
        expires_at=expires_at,
        issued_at=issued_at
    )
