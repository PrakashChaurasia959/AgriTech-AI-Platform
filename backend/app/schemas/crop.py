"""Crop recommendation Pydantic schemas."""
from pydantic import BaseModel, Field
from datetime import datetime


class CropRecommendationRequest(BaseModel):
    nitrogen: float = Field(..., ge=0, le=200, description="Nitrogen (N) level in soil")
    phosphorus: float = Field(..., ge=0, le=200, description="Phosphorus (P) level in soil")
    potassium: float = Field(..., ge=0, le=200, description="Potassium (K) level in soil")
    temperature: float = Field(..., ge=-20, le=60, description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    rainfall: float = Field(..., ge=0, le=500, description="Rainfall in mm")
    soil_type: str = Field("Loamy", description="Soil type")
    location: str = Field("", description="Location / region")


class CropRecommendationItem(BaseModel):
    crop: str
    confidence: float
    suitability: str
    description: str
    farming_tips: list[str]
    fertilizer_suggestions: list[str]


class CropRecommendationResponse(BaseModel):
    recommendations: list[CropRecommendationItem]
    top_recommendation: str
    soil_info: dict
    prediction_id: str
    created_at: datetime


class CropHistoryItem(BaseModel):
    id: str
    top_recommendation: str
    nitrogen: float
    phosphorus: float
    potassium: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float
    created_at: datetime
