from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TypeSol(str, Enum):
    ARGILEUX = "argileux"
    SABLEUX = "sableux"
    LIMONEUX = "limoneux"
    HUMIFERE = "humifère"
    CALCAIRE = "calcaire"
    TOURBEUX = "tourbeux"


class StatutParcelle(str, Enum):
    ACTIVE = "active"
    EN_CULTURE = "en_culture"
    EN_JACHERE = "en_jachère"
    EN_PREPARATION = "en_préparation"
    RECOLTE_EN_COURS = "récolte_en_cours"


class SystemeIrrigation(str, Enum):
    GOUTTE_A_GOUTTE = "goutte_à_goutte"
    ASPERSION = "aspersion"
    GRAVITAIRE = "gravitaire"
    PIVOT = "pivot"
    AUCUN = "aucun"


class CoordinatePoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class CaracteristiquesSol(BaseModel):
    type_sol: TypeSol



class ParcelleBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    terrain_id: str
    superficie: float = Field(..., gt=0)
    systeme_irrigation: Optional[SystemeIrrigation] = None
    source_eau: Optional[str] = Field(None, max_length=200)


class ParcelleCreate(ParcelleBase):
    pass


class ParcelleUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    statut: Optional[StatutParcelle] = None
    superficie: Optional[float] = Field(None, gt=0)
    systeme_irrigation: Optional[SystemeIrrigation] = None
    culture_actuelle_id: Optional[str] = None
    date_plantation: Optional[datetime] = None


class ParcelleResponse(BaseModel):
    id: str
    nom: str
    code: Optional[str]
    description: Optional[str]
    terrain_id: str
    superficie: float
    type_sol: TypeSol
    statut: StatutParcelle
    culture_actuelle_id: Optional[str]
    date_plantation: Optional[datetime]
    date_recolte_estimee: Optional[datetime]
    systeme_irrigation: Optional[SystemeIrrigation]
    nombre_capteurs: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True