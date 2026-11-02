"""Application configuration using Pydantic Settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Smart Agriculture API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # Security
    JWT_SECRET: str = "CHANGE_ME_TO_A_RANDOM_SECRET_KEY_AT_LEAST_64_CHARS_LONG"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "smart_agriculture_db"

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Admin
    ADMIN_EMAIL: str = "admin@smartagri.com"
    ADMIN_PASSWORD: str = "admin123456"

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@smartagri.com"

    # Weather (Open-Meteo - free, no key required)
    WEATHER_API_BASE: str = "https://api.open-meteo.com/v1"

    # OpenWeatherMap - live weather auto-fill
    # Key from https://openweathermap.org/api (new keys activate in ~2 hours)
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE: str = "https://api.openweathermap.org/data/2.5"

    # Kaggle API - for PlantVillage CNN training
    KAGGLE_API_TOKEN: str = ""

    # Production flag
    PRODUCTION: bool = False
    # MongoDB alias (MONGO_URI maps to MONGODB_URL)
    MONGO_URI: str = ""

    # ML - Disease detection
    DISEASE_MODEL_MODE: str = "demo"
    DISEASE_MODEL_PATH: str = "ml_models/agrivision_model.h5"
    DISEASE_MODEL_INPUT_SIZE: int = 256
    DISEASE_MODEL_NUM_CLASSES: int = 38

    # ML - Crop recommendation
    CROP_MODEL_PATH: str = "ml_models/crop_recommendation_model.pkl"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def owm_configured(self) -> bool:
        return bool(self.OPENWEATHER_API_KEY and self.OPENWEATHER_API_KEY.strip())

    @property
    def kaggle_configured(self) -> bool:
        return bool(self.KAGGLE_API_TOKEN and self.KAGGLE_API_TOKEN.strip())


settings = Settings()


