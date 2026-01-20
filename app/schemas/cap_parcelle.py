from typing import Optional
from datetime import datetime
from pydantic import ConfigDict
from app.schemas.common import ResponseBase

class CapParcelle(ResponseBase):
    """
    Schema for the association between a sensor (capteur) and a plot (parcelle).
    """
    capteur_id: str
    parcelle_id: str
    date_assignation: datetime
    date_desassignation: Optional[datetime] = None
    id: str

    model_config = ConfigDict(from_attributes=True)
