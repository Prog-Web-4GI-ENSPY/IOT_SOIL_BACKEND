from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid


# The base class which all models will inherit from
Base = declarative_base()

class BaseModel(Base):
    """
    Base model class with common fields.
    """
    __abstract__ = True  # Tells SQLAlchemy not to create a table for this class

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)