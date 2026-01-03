from typing import Optional, List
from pydantic import Field, AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=True,
        
    )
    
    # --- Application ---
    APP_NAME: str = Field(default="AgroPredict API")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = Field(default="/api/v1")
    
    # --- Database (Ajout des champs pour la construction de l'URL) ---
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None

    # L'URL finale de la DB. Pydantic peut la valider si le type est AnyUrl.
    # Elle sera lue depuis .env OU construite via la post-initialisation.
    DATABASE_URL: Optional[AnyUrl] = None
    
    # --- Security ---
    SECRET_KEY: str
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # --- ChirpStack ---
    CHIRPSTACK_API_URL: AnyUrl
    CHIRPSTACK_API_TOKEN: str
    CHIRPSTACK_APPLICATION_ID: str

    # --- AI Services ---
    EXPERT_SYSTEM_URL: AnyUrl = Field(default="https://systeme-expert-5iyu.onrender.com")
    ML_SERVICE_URL: AnyUrl = Field(default="https://crops-predictions.onrender.com")

    # --- CORS ---
    # Utilisez 'List' ou 'list' (avec Pydantic v2) pour les listes
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])


    # --- Méthode de construction post-initialisation ---
    def model_post_init(self, __context: any) -> None:
        """
        Méthode appelée après l'initialisation du modèle.
        Permet de construire DATABASE_URL si elle n'est pas fournie 
        mais que les composants sont là.
        """
        if self.DATABASE_URL is None and self.POSTGRES_USER and self.POSTGRES_DB:
            # Construit l'URL à partir des composants
            # Fallback sûr pour l'URL si elle n'est pas définie dans .env
            self.DATABASE_URL = AnyUrl.build(
                scheme="postgresql",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER or "localhost",
                port=self.POSTGRES_PORT,
                path=f"/{self.POSTGRES_DB}",
            )


settings = Settings()