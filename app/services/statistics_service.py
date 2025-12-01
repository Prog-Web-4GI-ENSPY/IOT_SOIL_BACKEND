from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from datetime import datetime, timedelta


class StatisticsService:
    
    def get_dashboard_stats(
        self,
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """Obtenir les statistiques du dashboard"""
        from app.models.terrain import Terrain
        from app.models.parcelle import Parcelle
        from app.models.capteur import Capteur, StatutCapteur
        from app.models.alert import Alerte
        
        # Nombre de terrains
        nb_terrains = db.query(func.count(Terrain.id)).filter(
            Terrain.user_id == user_id
        ).scalar()
        
        # Nombre de parcelles
        nb_parcelles = db.query(func.count(Parcelle.id)).join(
            Terrain
        ).filter(Terrain.user_id == user_id).scalar()
        
        # Nombre de capteurs actifs
        nb_capteurs_actifs = db.query(func.count(Capteur.id)).join(
            Parcelle
        ).join(Terrain).filter(
            Terrain.user_id == user_id,
            Capteur.statut == StatutCapteur.ONLINE
        ).scalar()
        
        # Nombre d'alertes non résolues
        nb_alertes = db.query(func.count(Alerte.id)).filter(
            Alerte.user_id == user_id,
            Alerte.est_resolue == False
        ).scalar()
        
        return {
            "terrains": nb_terrains,
            "parcelles": nb_parcelles,
            "capteurs_actifs": nb_capteurs_actifs,
            "alertes": nb_alertes
        }


statistics_service = StatisticsService()
