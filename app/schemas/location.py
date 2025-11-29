from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class Continent(str, Enum):
    AFRIQUE = "Afrique"
    AMERIQUE_NORD = "Amérique du Nord"
    AMERIQUE_SUD = "Amérique du Sud"
    ASIE = "Asie"
    EUROPE = "Europe"
    OCEANIE = "Océanie"
    ANTARCTIQUE = "Antarctique"


class ClimateZone(str, Enum):
    TROPICAL = "tropical"
    SUBTROPICAL = "subtropical"
    TEMPERATE = "temperate"
    CONTINENTAL = "continental"
    ARID = "arid"
    SEMI_ARID = "semi-arid"
    MEDITERRANEAN = "mediterranean"


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None


class Address(BaseModel):
    quartier: Optional[str] = None
    ville: str = Field(..., min_length=2, max_length=200)
    region: Optional[str] = None
    pays: str = Field(..., min_length=2, max_length=100)
    code_postal: Optional[str] = None
    continent: Continent


class LocaliteBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    coordinates: Coordinates
    address: Address
    timezone: str = Field(..., max_length=50)
    superficie: Optional[float] = Field(None, gt=0)
    population: Optional[int] = Field(None, gt=0)
    climate_zone: Optional[ClimateZone] = None


class LocaliteCreate(LocaliteBase):
    pass


class LocaliteUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    timezone: Optional[str] = None
    superficie: Optional[float] = Field(None, gt=0)
    population: Optional[int] = Field(None, gt=0)
    climate_zone: Optional[ClimateZone] = None


class LocaliteResponse(BaseModel):
    id: str
    nom: str
    latitude: float
    longitude: float
    altitude: Optional[float]
    quartier: Optional[str]
    ville: str
    region: Optional[str]
    pays: str
    code_postal: Optional[str]
    continent: Continent
    timezone: str
    superficie: Optional[float]
    population: Optional[int]
    climate_zone: Optional[ClimateZone]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True