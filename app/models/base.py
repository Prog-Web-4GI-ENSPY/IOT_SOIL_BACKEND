from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

# Fonction pour générer un UUID hexadécimal (ou la méthode que vous utilisez)
def generate_uuid_as_string():
    return str(uuid.uuid4())

class BaseModel(Base):
    """
    Base model class with UUID primary key.
    """
    __abstract__ = True 

    # CLÉ PRIMAIRE DÉFINIE COMME STRING DE 36 CARACTÈRES (UUID)
    id = Column(String(36), primary_key=True, index=True, default=generate_uuid_as_string)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)