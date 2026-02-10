from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.user import NotificationMode

class NotificationTestRequest(BaseModel):
    mode: NotificationMode
    target: Optional[str] = Field(None, description="Email, téléphone ou chat_id. Si vide, utilise les données de l'utilisateur connecté.")
    message: str = "Ceci est un test de notification AgroPredict."

class NotificationResponse(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None
