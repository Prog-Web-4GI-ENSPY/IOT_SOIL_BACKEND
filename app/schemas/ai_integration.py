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
    """Réponse du service ML synchronisée avec l'API Render"""
    recommended_crop: str  # Au lieu de majority_crop
    confidence: float
    total_samples: int     # Au lieu de sample_count
    features_order: List[str]
    all_predictions: List[str]
    vote_details: Dict[str, int]

class ExpertSystemRequest(BaseModel):
    """Schéma requis par ExpertSystemService pour l'import"""
    query: str
    region: str = "Centre"

class ExpertSystemResponse(BaseModel):
    """Réponse du Système Expert"""
    final_response: str
    query: str
    region: str
    orchestration: Optional[Dict[str, Any]] = None



class UnifiedRecommendationRequest(BaseModel):
    """Requête combinée du frontend"""
    soil_data: SoilData
    region: Optional[str] = "Centre"
    query: Optional[str] = Field(None, description="Question spécifique pour le système expert")
    parcelle_id: Optional[str] = Field(None, description="ID de la parcelle pour stocker la recommandation")

class UnifiedRecommendationResponse(BaseModel):
    """Réponse unifiée et agrégée"""
    recommended_crop: str
    confidence_score: float
    justification: str
    ml_details: MLPredictResponse
    expert_details: Optional[ExpertSystemResponse] = None
    generated_at: str

class ParcellePredictionRequest(BaseModel):
    """Requête simplifiée pour la prédiction par parcelle"""
    region: Optional[str] = "Centre"
    query: Optional[str] = Field(None, description="Question spécifique pour le système expert")

