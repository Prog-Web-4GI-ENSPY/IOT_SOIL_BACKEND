from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TypeTerrain(str, Enum):
    AGRICOLE = "agricole"
    PASTORAL = "pastoral"
    MIXTE = "mixte"
    EXPERIMENTAL = "experimental"


class StatutTerrain(str, Enum):
    ACTIF = "actif"
    EN_JACHERE = "en_jachère"
    EN_PREPARATION = "en_préparation"
    ABANDONNE = "abandonné"


class TerrainBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    type_terrain: TypeTerrain
    localite_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    superficie_totale: float = Field(..., gt=0)
    perimetre: Optional[float] = Field(None, gt=0)
    pente: Optional[float] = Field(None, ge=0, le=90)
    date_acquisition: Optional[datetime] = None


class TerrainCreate(TerrainBase):
    pass


class TerrainUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    type_terrain: Optional[TypeTerrain] = None
    statut: Optional[StatutTerrain] = None
    superficie_totale: Optional[float] = Field(None, gt=0)
    perimetre: Optional[float] = Field(None, gt=0)


class TerrainResponse(TerrainBase):
    id: str
    statut: StatutTerrain
    user_id: str
    nombre_parcelles: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True