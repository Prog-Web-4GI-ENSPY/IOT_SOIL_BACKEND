from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User, UserStatus, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service pour la gestion des utilisateurs"""

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Recupere un utilisateur par son ID

        Args:
            db: Session de base de donnees
            user_id: ID de l'utilisateur

        Returns:
            User ou None si non trouve
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        R�cup�re un utilisateur par son email

        Args:
            db: Session de base de donn�es
            email: Email de l'utilisateur

        Returns:
            User ou None si non trouv�
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Cr�e un nouvel utilisateur

        Args:
            db: Session de base de donn�es
            user_data: Donn�es de l'utilisateur � cr�er

        Returns:
            User cr��

        Raises:
            HTTPException: Si l'email existe d�j�
        """
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
            role=user_data.role,
            status=UserStatus.ACTIVE,
            preferences=user_data.preferences.dict() if user_data.preferences else None,
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
        """
        Met � jour un utilisateur

        Args:
            db: Session de base de donn�es
            user_id: ID de l'utilisateur
            user_data: Donn�es de mise � jour

        Returns:
            User mis � jour

        Raises:
            HTTPException: Si l'utilisateur n'existe pas
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = user_data.dict(exclude_unset=True)

        if "preferences" in update_data and update_data["preferences"]:
            update_data["preferences"] = update_data["preferences"].dict()

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """
        Supprime un utilisateur

        Args:
            db: Session de base de donn�es
            user_id: ID de l'utilisateur

        Returns:
            True si supprim� avec succ�s

        Raises:
            HTTPException: Si l'utilisateur n'existe pas
        """
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
        """
        Authentifie un utilisateur

        Args:
            db: Session de base de donn�es
            email: Email de l'utilisateur
            password: Mot de passe

        Returns:
            User si l'authentification r�ussit, None sinon
        """
        user = UserService.get_user_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        old_password: str,
        new_password: str
    ) -> User:
        """
        Change le mot de passe d'un utilisateur

        Args:
            db: Session de base de donn�es
            user: Utilisateur
            old_password: Ancien mot de passe
            new_password: Nouveau mot de passe

        Returns:
            User mis � jour

        Raises:
            HTTPException: Si l'ancien mot de passe est incorrect
        """
        if not verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )

        user.password_hash = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_last_access(db: Session, user: User) -> User:
        """
        Met � jour la date du dernier acc�s

        Args:
            db: Session de base de donn�es
            user: Utilisateur

        Returns:
            User mis � jour
        """
        user.dernier_acces = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_user_status(
        db: Session,
        user_id: str,
        new_status: UserStatus
    ) -> User:
        """
        Change le statut d'un utilisateur

        Args:
            db: Session de base de donn�es
            user_id: ID de l'utilisateur
            new_status: Nouveau statut

        Returns:
            User mis � jour

        Raises:
            HTTPException: Si l'utilisateur n'existe pas
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_user.status = new_status
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[UserStatus] = None,
        role: Optional[UserRole] = None
    ) -> list[User]:
        """
        R�cup�re tous les utilisateurs avec filtres optionnels

        Args:
            db: Session de base de donn�es
            skip: Nombre d'utilisateurs � sauter
            limit: Nombre maximum d'utilisateurs � retourner
            status: Filtre par statut
            role: Filtre par r�le

        Returns:
            Liste d'utilisateurs
        """
        query = db.query(User)

        if status:
            query = query.filter(User.status == status)
        if role:
            query = query.filter(User.role == role)

        return query.offset(skip).limit(limit).all()
