from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

# Fonction pour générer un UUID hexadécimal (ou la méthode que vous utilisez)
def generate_uuid_as_string():
    return str(uuid.uuid4())

class BaseModel(Base):
    """class BaseModel(Base):
    """
    Base model class with UUID primary key.
    """
    __abstract__ = True 

    # CLÉ PRIMAIRE DÉFINIE COMME STRING DE 36 CARACTÈRES (UUID)
    id = Column(String(36), primary_key=True, index=True, default=generate_uuid_as_string)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
class BaseModel(Base):
    """
    Base model class with UUID primary key.
    """
    __abstract__ = True 

    # CLÉ PRIMAIRE DÉFINIE COMME STRING DE 36 CARACTÈRES (UUID)
    id = Column(String(36), primary_key=True, index=True, default=generate_uuid_as_string)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    Base model class with UUID primary key.
    """
    __abstract__ = True 

    # CLÉ PRIMAIRE DÉFINIE COMME STRING DE 36 CARACTÈRES (UUID)
    id = Column(String(36), primary_key=True, index=True, default=generate_uuid_as_string)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, default=None)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def restore(self):
        self.deleted_at = None
        self.updated_at = datetime.utcnow()