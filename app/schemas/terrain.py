from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TerrainBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    localite_id: str
    superficie: Optional[float] = Field(None, gt=0)


class TerrainCreate(TerrainBase):
    pass


class TerrainUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    superficie: Optional[float] = Field(None, gt=0)


class TerrainResponse(TerrainBase):
    id: str
    user_id: str
    nombre_parcelles: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True