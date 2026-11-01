"""Disease detection Pydantic schemas."""
from pydantic import BaseModel
from datetime import datetime


class DiseasePredictionResponse(BaseModel):
    disease_name: str
    confidence: float
    is_healthy: bool
    crop_type: str
    symptoms: list[str]
    causes: list[str]
    treatment: list[str]
    prevention: list[str]
    image_url: str | None = None
    prediction_id: str
    is_demo_mode: bool
    created_at: datetime


class DiseaseHistoryItem(BaseModel):
    id: str
    crop_type: str
    disease_name: str
    confidence: float
    is_healthy: bool
    is_demo_mode: bool
    created_at: datetime
