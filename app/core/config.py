from typing import Optional, List
from pydantic import Field, AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'  # Par défaut, ignore les champs supplémentaires
    )
    
    # --- Application ---
    APP_NAME: str = Field(default="AgroPredict API")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = Field(default="/api/v1")
    API_PREFIX: str = Field(default="/api/v1")  # Ajouté
    
    # --- Database ---
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # --- Security ---
    SECRET_KEY: str
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # --- ChirpStack ---
    CHIRPSTACK_API_URL: Optional[str] = None
    CHIRPSTACK_API_TOKEN: Optional[str] = None
    CHIRPSTACK_APPLICATION_ID: Optional[str] = None

    # --- AI Services ---
    EXPERT_SYSTEM_URL: str = Field(default="https://systeme-expert-5iyu.onrender.com")
    ML_SERVICE_URL: str = Field(default="https://crops-predictions.onrender.com")

    # --- CORS ---
    # Utilisez 'List' ou 'list' (avec Pydantic v2) pour les listes
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["https://smart-agro-three.vercel.app","https://administrative-part-of-smart-agri-i.vercel.app","http://localhost:3000","http://localhost:3001"])


    # --- Méthode de construction post-initialisation ---
    def model_post_init(self, __context: any) -> None:
        """Construit DATABASE_URL si elle n'est pas fournie."""
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
