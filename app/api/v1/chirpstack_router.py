"""
Router pour les webhooks ChirpStack
"""
from fastapi import APIRouter, Depends, status, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
import uuid
from datetime import datetime

from app.database import get_db
from app.models.sensor_data import SensorMeasurements
from app.models.capteur import Capteur
from app.models.parcelle import Parcelle

router = APIRouter(
    prefix="/chirpstack",
    tags=["ChirpStack"]
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Traiter une chaîne de segments concaténés"
)
async def process_raw_sensor_data(
    payload: Dict[str, str] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint unique pour traiter le contenu brut.
    """
    content = payload.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Le contenu est vide")

    # Split par virgule et nettoyage
    segments = [s.strip() for s in content.split(",") if s.strip()]
    
    aggregated_data = {}
    # 1:hum, 2:temp, 3:ph, 4:n, 5:p, 6:k
    mapping = {1: "humidity", 2: "temperature", 3: "ph", 4: "azote", 5: "phosphore", 6: "potassium"}

    try:
        for seg in segments:
            # Nettoyage des espaces doubles internes
            parts = [p for p in seg.split(" ") if p]
            
            if len(parts) < 3:
                continue

            # Extraction d:valeur
            valeur = float(parts[0].split(":")[1])
            
            # Extraction s:code;indice
            sensor_info = parts[1].split(":")[1]
            capteur_code, indice_str = sensor_info.split(";")
            indice = int(indice_str)
            
            # Extraction p:code
            parcelle_code = parts[2].split(":")[1]

            key = (capteur_code, parcelle_code)
            if key not in aggregated_data:
                aggregated_data[key] = {"metrics": {}}
            
            if indice in mapping:
                aggregated_data[key]["metrics"][mapping[indice]] = valeur

        created_records = []
        for (c_code, p_code), data in aggregated_data.items():
            # 1. Vérification de l'existence du capteur
            capteur = db.query(Capteur).filter(Capteur.code == c_code).first()
            if not capteur:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Le capteur avec le code '{c_code}' n'existe pas dans la base de données."
                )

            # 2. Vérification de l'existence de la parcelle
            parcelle = db.query(Parcelle).filter(Parcelle.code == p_code).first()
            if not parcelle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"La parcelle avec le code '{p_code}' n'existe pas dans la base de données."
                )

            # 3. Si les deux existent, on crée l'enregistrement
            new_meas = SensorMeasurements(
                id=str(uuid.uuid4()),
                capteur_id=capteur.id,
                parcelle_id=parcelle.id,
                timestamp=datetime.utcnow(),
                humidity=data["metrics"].get("humidity"),
                temperature=data["metrics"].get("temperature"),
                ph=data["metrics"].get("ph"),
                azote=data["metrics"].get("azote"),
                phosphore=data["metrics"].get("phosphore"),
                potassium=data["metrics"].get("potassium"),
                measurements=data["metrics"]
            )
            db.add(new_meas)
            created_records.append(new_meas)

        db.commit()
        return {
            "status": "success", 
            "records_created": len(created_records)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur de formatage: {str(e)}")