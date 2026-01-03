from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SoilData(BaseModel):
    """Données du sol pour les prédictions"""
    N: int = Field(..., description="Azote (Nitrogen)")
    P: int = Field(..., description="Phosphore (Phosphorus)")
    K: int = Field(..., description="Potassium")
    temperature: float = Field(..., description="Température en °C")
    humidity: float = Field(..., description="Humidité relative en %")
    ph: float = Field(..., description="Niveau de pH du sol")

class MLSample(SoilData):
    """Un échantillon pour le service ML"""
    pass

class MLPredictRequest(BaseModel):
    """Requête pour le service ML /predict/batch"""
    samples: List[MLSample] = Field(..., max_items=10)

class MLPredictResponse(BaseModel):
    """Réponse du service ML"""
    majority_crop: str
    predictions: List[str]
    confidence: float
    sample_count: int

class ExpertSystemRequest(BaseModel):
    """Requête pour le Système Expert /api/query"""
    query: str
    region: str = "Centre"

class ExpertSystemResponse(BaseModel):
    """Réponse du Système Expert"""
    final_response: str
    orchestration: Dict[str, Any]
    query: str
    region: str

class UnifiedRecommendationRequest(BaseModel):
    """Requête combinée du frontend"""
    soil_data: SoilData
    region: Optional[str] = "Centre"
    parcelle_id: Optional[str] = Field(None, description="ID de la parcelle pour stocker la recommandation")

class UnifiedRecommendationResponse(BaseModel):
    """Réponse unifiée et agrégée"""
    recommended_crop: str
    confidence_score: float
    justification: str
    ml_details: MLPredictResponse
    expert_details: Optional[ExpertSystemResponse] = None
    generated_at: str
