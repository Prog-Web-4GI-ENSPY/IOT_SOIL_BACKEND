from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CoordinatePoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ParcelleBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    terrain_id: str
    superficie: float = Field(..., gt=0)


class ParcelleCreate(ParcelleBase):
    """Schéma pour la création d'une parcelle (le code est généré automatiquement)"""
    pass


class ParcelleUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    superficie: Optional[float] = Field(None, gt=0)


class ParcelleResponse(BaseModel):
    id: str
    nom: str
    code: Optional[str]
    description: Optional[str]
    terrain_id: str
    superficie: float
    nombre_capteurs: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True