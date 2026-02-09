from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class NotificationMode(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    TELEGRAM = "telegram"


class UserBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telephone: Optional[str] = Field(None, max_length=20)
    notification_modes: List[NotificationMode] = Field(default_factory=lambda: [NotificationMode.EMAIL])


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        if not any(char.isdigit() for char in v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not any(char.isupper() for char in v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        return v


class UserUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=100)
    prenom: Optional[str] = Field(None, min_length=2, max_length=100)
    telephone: Optional[str] = None
    avatar: Optional[str] = None
    notification_modes: Optional[List[NotificationMode]] = None


class UserResponse(BaseModel):
    id: str
    nom: str
    prenom: str
    email: EmailStr
    telephone: Optional[str]
    role: UserRole
    avatar: Optional[str] = None
    notification_modes: List[NotificationMode] = []
    date_inscription: datetime
    dernier_acces: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
