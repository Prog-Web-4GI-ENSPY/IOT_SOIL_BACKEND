from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class NotificationPreferences(BaseModel):
    email: bool = True
    push: bool = True
    sms: bool = False


class UnitePreferences(BaseModel):
    temperature: str = "celsius"  # celsius | fahrenheit
    surface: str = "hectare"  # hectare | acre
    precipitation: str = "mm"  # mm | inch


class UserPreferences(BaseModel):
    langue: str = "fr"  # fr | en | es
    theme: str = "light"  # light | dark | auto
    notifications: NotificationPreferences = NotificationPreferences()
    unites: UnitePreferences = UnitePreferences()


class UserBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    prenom: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    telephone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.USER
    preferences: Optional[UserPreferences] = None


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
    preferences: Optional[UserPreferences] = None


class UserResponse(UserBase):
    id: str
    status: UserStatus
    avatar: Optional[str] = None
    date_inscription: datetime
    dernier_acces: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
