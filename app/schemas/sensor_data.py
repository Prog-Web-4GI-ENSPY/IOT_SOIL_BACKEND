from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class SensorMeasurementsBase(BaseModel):
    ph: Optional[float] = None
    azote: Optional[float] = Field(None, description="Quantité d'azote en kg/ha")
    phosphore: Optional[float] = Field(None, description="Quantité de phosphore en kg/ha")
    potassium: Optional[float] = Field(None, description="Quantité de potassium en kg/ha")
    humidity: Optional[float] = None
    temperature: Optional[float] = Field(None, description="Température en °C")
    capteur_id: str
    timestamp: Optional[datetime] = None
    measurements: dict
    parcelle_id: str
    


class SensorMeasurementsCreate(SensorMeasurementsBase):
    @validator('measurements')
    def validate_measurements(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Measurements doit être un dictionnaire JSON')
        return v
    
class SensorMeasurementsUpdate(SensorMeasurementsBase):
    @validator('measurements')
    def validate_measurements(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Measurements doit être un dictionnaire JSON')
        return v

class SensorMeasurementsResponse(BaseModel):
    id: str
    ph: Optional[float]
    azote: Optional[float]
    phosphore: Optional[float]
    potassium: Optional[float]
    humidity: Optional[float]
    temperature: Optional[float]
    capteur_id: str
    timestamp: datetime
    measurements: dict
    parcelle_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 