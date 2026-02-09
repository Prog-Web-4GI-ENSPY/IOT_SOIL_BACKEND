from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class NotificationMode(str, enum.Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    TELEGRAM = "telegram"


class RecommendationFrequency(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    DISABLED = "disabled"


class User(BaseModel):
    __tablename__ = "users"

    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telephone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    avatar = Column(String(500))
    notification_modes = Column(JSON, default=list, nullable=False)  # ["email", "sms", "telegram"]
    recommendation_frequency = Column(SQLEnum(RecommendationFrequency), default=RecommendationFrequency.WEEKLY, nullable=False)
    date_inscription = Column(DateTime, default=datetime.utcnow, nullable=False)
    dernier_acces = Column(DateTime)
    

    # Relations
    terrains = relationship("Terrain", back_populates="proprietaire", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")

