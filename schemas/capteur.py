from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

class CapteurBase(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    dev_eui: str = Field(..., min_length=16, max_length=16)
    parcelle_id: str
    date_installation: datetime
    date_activation: Optional[datetime] = None

    @validator('dev_eui')
    def validate_hex_string(cls, v):
        if v and not re.match(r'^[0-9A-Fa-f]+$', v):
            raise ValueError('Doit être une chaîne hexadécimale')
        return v.upper() if v else v


class CapteurCreate(CapteurBase):
    pass

class CapteurUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=2, max_length=200)
    date_activation: Optional[datetime] = None

class CapteurResponse(BaseModel):
    id: str
    nom: str
    dev_eui: str
    parcelle_id: str
    date_installation: datetime
    date_activation: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True