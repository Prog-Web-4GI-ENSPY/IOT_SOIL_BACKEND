from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Schéma pour la requête de connexion"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schéma pour la réponse contenant les tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schéma pour les données extraites du token"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schéma pour la requête de rafraîchissement du token"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schéma pour la requête de changement de mot de passe"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordResetRequest(BaseModel):
    """Schéma pour la requête de réinitialisation de mot de passe"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schéma pour la confirmation de réinitialisation de mot de passe"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class TokenValidationRequest(BaseModel):
    """Schéma pour la requête de validation du token"""
    token: str


class TokenValidationResponse(BaseModel):
    """Schéma pour la réponse de validation du token"""
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
