from sqlalchemy import Column, String, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel


class Continent(str, enum.Enum):
    AFRIQUE = "Afrique"
    AMERIQUE_NORD = "Amérique du Nord"
    AMERIQUE_SUD = "Amérique du Sud"
    ASIE = "Asie"
    EUROPE = "Europe"
    OCEANIE = "Océanie"
    ANTARCTIQUE = "Antarctique"


class ClimateZone(str, enum.Enum):
    TROPICAL = "tropical"
    SUBTROPICAL = "subtropical"
    TEMPERATE = "temperate"
    CONTINENTAL = "continental"
    ARID = "arid"
    SEMI_ARID = "semi-arid"
    MEDITERRANEAN = "mediterranean"


class Localite(BaseModel):
    __tablename__ = "localites"

    nom = Column(String(200), nullable=False, index=True)
    
    population= Column(Float)



    
    # Adresse
    quartier = Column(String(200))
    ville = Column(String(200), nullable=False, index=True)
    region = Column(String(200))
    pays = Column(String(100), nullable=False, index=True)
    code_postal = Column(String(20))
    continent = Column(SQLEnum(Continent), nullable=False)
    
    climate_zone=Column(SQLEnum(ClimateZone))
    # Informations supplémentaires
    timezone = Column(String(50))
    superficie = Column(Float, nullable=False)  # km²
    

    # Relations
    terrains = relationship("Terrain", back_populates="localite")

