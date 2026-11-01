"""Application configuration using Pydantic Settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env.

    All fields are defined exactly ONCE.
    Duplicate definitions have been removed (they caused Pydantic v2 warnings
    and the last value silently shadowed earlier ones).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "Smart Agriculture API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # ── Security ──────────────────────────────────────────────────────────────
    JWT_SECRET: str = "CHANGE_ME_TO_A_RANDOM_SECRET_KEY_AT_LEAST_64_CHARS_LONG"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── MongoDB ───────────────────────────────────────────────────────────────
    # Primary connection — should be the Atlas URI.
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "smart_agriculture_db"
    # MONGODB_FALLBACK_URL is intentionally left out.
    # The application must connect to the configured database or FAIL — it must
    # never silently switch to a different data store.

    # ── CORS ──────────────────────────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Admin bootstrap ───────────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@smartagri.com"
    ADMIN_PASSWORD: str = "admin123456"

    # ── Email (SMTP) ──────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@smartagri.com"

    # ── Weather (Open-Meteo — free, no key required) ──────────────────────────
    WEATHER_API_BASE: str = "https://api.open-meteo.com/v1"

    # ── OpenWeatherMap (live weather auto-fill on crop page) ──────────────────
    # Free tier key from https://openweathermap.org/api
    # Leave empty to skip live weather auto-fill (sliders stay manual)
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE: str = "https://api.openweathermap.org/data/2.5"

    # ── ML — Disease detection ─────────────────────────────────────────────────
    # "demo"       → OpenCV colour-statistics fallback (no trained model needed)
    # "production" → Real Keras CNN loaded from DISEASE_MODEL_PATH
    DISEASE_MODEL_MODE: str = "demo"
    # Path to trained CNN (.keras or .h5), relative to backend/ or absolute
    DISEASE_MODEL_PATH: str = "ml_models/plant_disease_model.keras"
    # Input spatial size expected by the CNN (e.g. 224 for MobileNetV2)
    DISEASE_MODEL_INPUT_SIZE: int = 224
    # Number of output classes (PlantVillage = 38)
    DISEASE_MODEL_NUM_CLASSES: int = 38

    # ── ML — Crop recommendation ───────────────────────────────────────────────
    # Optional path to a pre-trained sklearn pkl / joblib.
    # If absent the backend auto-trains a Random Forest at startup.
    CROP_MODEL_PATH: str = "ml_models/crop_recommendation_model.pkl"

    # ── ML — Yield prediction ─────────────────────────────────────────────────
    # (yield model is always auto-trained from agronomic data; no external path needed)

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS origins string into a list."""
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
