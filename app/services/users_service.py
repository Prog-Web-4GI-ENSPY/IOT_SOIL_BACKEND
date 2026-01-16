from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service pour la gestion des utilisateurs"""

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Recupere un utilisateur par son ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Recupere un utilisateur par son email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate, role: UserRole = UserRole.USER) -> User:
        """Cree un nouvel utilisateur"""
        existing_user = UserService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(user_data.password)

        db_user = User(
            nom=user_data.nom,
            prenom=user_data.prenom,
            email=user_data.email,
            telephone=user_data.telephone,
            password_hash=hashed_password,
            role=role,
            date_inscription=datetime.utcnow()
        )

        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed"
            )

    @staticmethod
    def update_user(db: Session, user_id: str, user_data: UserUpdate) -> User:
        """Met a jour un utilisateur"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_user, field, value)

        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Update failed: {str(e)}"
            )

    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """Supprime un utilisateur"""
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db.delete(db_user)
        db.commit()
        return True

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        
        # Mise a jour du dernier acces
        user.dernier_acces = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        old_password_param: str,
        new_password: str
    ) -> User:
        """Change le mot de passe d'un utilisateur"""
        if not verify_password(old_password_param, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        user.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None
    ) -> List[User]:
        """Recupere tous les utilisateurs"""
        query = db.query(User)

        if role:
            query = query.filter(User.role == role)

        return query.offset(skip).limit(limit).all()
