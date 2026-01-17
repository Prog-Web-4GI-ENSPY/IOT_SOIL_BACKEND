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
    BACKEND_CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:3001"])
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000"])  # Ajouté

    # --- Twilio / SMS ---
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_VERIFY_SERVICE_SID: Optional[str] = None
    SMS_PROVIDER: str = Field(default="twilio")
    DEFAULT_SMS_SENDER: str = Field(default="MONAPP")
    MAX_SMS_PER_DAY: int = Field(default=100)
    
    # --- Email ---
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    
    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    def model_post_init(self, __context: any) -> None:
        """Construit DATABASE_URL si elle n'est pas fournie."""
        if self.DATABASE_URL is None and self.POSTGRES_USER and self.POSTGRES_DB:
            password = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
            port = f":{self.POSTGRES_PORT}" if self.POSTGRES_PORT else ""
            host = self.POSTGRES_SERVER or "localhost"
            
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}{password}@{host}{port}/{self.POSTGRES_DB}"


# Juste cette ligne, RIEN après
settings = Settings()