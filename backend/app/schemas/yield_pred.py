"""Yield prediction Pydantic schemas."""
from pydantic import BaseModel, Field
from datetime import datetime


class YieldPredictionRequest(BaseModel):
    crop_type: str = Field(..., description="Crop type (e.g., rice, wheat, maize)")
    state: str = Field(..., description="State or region")
    season: str = Field(..., description="Season (e.g., Kharif, Rabi, Whole Year)")
    area: float = Field(..., gt=0, description="Area in hectares")
    rainfall: float = Field(..., ge=0, description="Rainfall in mm")
    temperature: float = Field(..., description="Average temperature in Celsius")
    soil_type: str = Field("Loamy", description="Soil type")
    fertilizer_usage: float = Field(0, ge=0, description="Fertilizer usage in kg/hectare")


class YieldPredictionResponse(BaseModel):
    crop_type: str
    predicted_yield: float
    predicted_production: float
    yield_unit: str
    confidence: float
    suitability: str
    conditions_summary: str
    improvement_suggestions: list[str]
    prediction_id: str
    created_at: datetime
    is_estimate: bool = True


class YieldHistoryItem(BaseModel):
    id: str
    crop_type: str
    state: str
    season: str
    area: float
    predicted_yield: float
    created_at: datetime
