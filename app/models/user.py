from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    __tablename__ = "users"

    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telephone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    avatar = Column(String(500))
    date_inscription = Column(DateTime, default=datetime.utcnow, nullable=False)
    dernier_acces = Column(DateTime)
    

    # Relations
    terrains = relationship("Terrain", back_populates="proprietaire", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")

