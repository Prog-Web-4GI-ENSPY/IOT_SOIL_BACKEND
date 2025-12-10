from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.alert import Alert, TypeAlerte, SeveriteAlerte
from app.models.user import User


class NotificationService:
    
    def create_alert(
        self,
        db: Session,
        user_id: str,
        type_alerte: TypeAlerte,
        severite: SeveriteAlerte,
        titre: str,
        message: str,
        parcelle_id: Optional[str] = None,
        capteur_id: Optional[str] = None,
        valeur_actuelle: Optional[float] = None,
        valeur_seuil: Optional[float] = None,
        unite: Optional[str] = None
    ) -> Alert:
        """Créer une nouvelle alerte"""
        alerte = Alert(
            user_id=user_id,
            parcelle_id=parcelle_id,
            capteur_id=capteur_id,
            type=type_alerte,
            severite=severite,
            titre=titre,
            message=message,
            valeur_actuelle=valeur_actuelle,
            valeur_seuil=valeur_seuil,
            unite=unite,
            est_lue=False,
            est_resolue=False,
            date_emission=datetime.utcnow()
        )
        
        db.add(alerte)
        db.commit()
        db.refresh(alerte)
        
        # TODO: Envoyer notification email/SMS/push selon préférences user
        
        return alerte
    
    def mark_as_read(
        self,
        db: Session,
        alert_id: str
    ) -> Alert:
        """Marquer une alerte comme lue"""
        alerte = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if alerte:
            alerte.est_lue = True
            db.commit()
            db.refresh(alerte)
        
        return alerte
    
    def resolve_alert(
        self,
        db: Session,
        alert_id: str
    ) -> Alert:
        """Résoudre une alerte"""
        alerte = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if alerte:
            alerte.est_resolue = True
            alerte.date_resolution = datetime.utcnow()
            db.commit()
            db.refresh(alerte)
        
        return alerte


notification_service = NotificationService()

