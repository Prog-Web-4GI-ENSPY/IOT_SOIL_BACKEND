from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.users_service import UserService
from app.core.dependencies import (
    get_current_active_user,
    require_admin,
    get_current_user
)
from app.models.user import User, UserStatus, UserRole

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère le profil de l'utilisateur connecté

    Args:
        current_user: L'utilisateur actuel

    Returns:
        UserResponse: Profil de l'utilisateur
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met à jour le profil de l'utilisateur connecté

    Args:
        user_data: Données de mise à jour
        current_user: L'utilisateur actuel
        db: Session de base de données

    Returns:
        UserResponse: Profil mis à jour
    """
    return UserService.update_user(db, str(current_user.id), user_data)


@router.get("/", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[UserStatus] = None,
    role: Optional[UserRole] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Récupère tous les utilisateurs (Admin uniquement)

    Args:
        skip: Nombre d'utilisateurs à sauter
        limit: Nombre maximum d'utilisateurs à retourner
        status: Filtre par statut
        role: Filtre par rôle
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        List[UserResponse]: Liste des utilisateurs
    """
    return UserService.get_all_users(db, skip, limit, status, role)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Récupère un utilisateur par son ID (Admin uniquement)

    Args:
        user_id: ID de l'utilisateur
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        UserResponse: L'utilisateur

    Raises:
        HTTPException: Si l'utilisateur n'existe pas
    """
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Met à jour un utilisateur (Admin uniquement)

    Args:
        user_id: ID de l'utilisateur
        user_data: Données de mise à jour
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        UserResponse: Utilisateur mis à jour
    """
    return UserService.update_user(db, user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Supprime un utilisateur (Admin uniquement)

    Args:
        user_id: ID de l'utilisateur
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        Statut 204 No Content

    Raises:
        HTTPException: Si l'utilisateur tente de se supprimer lui-même
    """
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    UserService.delete_user(db, user_id)
    return None


@router.patch("/{user_id}/status", response_model=UserResponse)
def change_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Change le statut d'un utilisateur (Admin uniquement)

    Args:
        user_id: ID de l'utilisateur
        new_status: Nouveau statut
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        UserResponse: Utilisateur avec le statut mis à jour

    Raises:
        HTTPException: Si l'utilisateur tente de changer son propre statut
    """
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )

    return UserService.change_user_status(db, user_id, new_status)


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Active un utilisateur (Admin uniquement)

    Args:
        user_id: ID de l'utilisateur
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        UserResponse: Utilisateur activé
    """
    return UserService.change_user_status(db, user_id, UserStatus.ACTIVE)


@router.patch("/{user_id}/suspend", response_model=UserResponse)
def suspend_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Suspend un utilisateur (Admin uniquement)

    Args:
        user_id: ID de l'utilisateur
        current_user: L'utilisateur actuel (doit être admin)
        db: Session de base de données

    Returns:
        UserResponse: Utilisateur suspendu

    Raises:
        HTTPException: Si l'utilisateur tente de se suspendre lui-même
    """
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot suspend your own account"
        )

    return UserService.change_user_status(db, user_id, UserStatus.SUSPENDED)
