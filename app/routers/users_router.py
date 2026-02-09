from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, NotificationMode
from app.services.users_service import UserService
from app.core.dependencies import (
    get_current_active_user,
    require_admin,
    get_current_user
)
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Recupere le profil de l'utilisateur connecte
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met a jour le profil de l'utilisateur connecte
    """
    return UserService.update_user(db, str(current_user.id), user_data)


@router.put("/me/notification-settings", response_model=UserResponse)
def update_notification_settings(
    notification_modes: List[NotificationMode] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Met a jour les modes de notification de l'utilisateur connecte
    """
    user_update = UserUpdate(notification_modes=notification_modes)
    return UserService.update_user(db, str(current_user.id), user_update)


@router.get("/", response_model=List[UserResponse])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Recupere tous les utilisateurs (Admin uniquement)
    """
    return UserService.get_all_users(db, skip, limit, role)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Recupere un utilisateur par son ID (Admin uniquement)
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
    Met a jour un utilisateur (Admin uniquement)
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
    """
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    UserService.delete_user(db, user_id)
    return None
