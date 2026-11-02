"""
Crop recommendation API routes.

Extra endpoint added:
  GET /api/crop/live-weather
    Accepts lat/lon, returns OpenWeatherMap current weather
    (temperature, humidity, precipitation in mm).
    Used by the frontend to auto-fill the climate sliders.
    Falls back to Open-Meteo when OpenWeatherMap is unavailable.
"""
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.deps import get_current_user
from app.schemas.crop import CropRecommendationRequest
from app.services.weather_service import get_current_weather
from app.services.crop_service import recommend_crop, get_crop_history, delete_crop_recommendation
from app.services.report_service import generate_crop_report

router = APIRouter(prefix="/crop", tags=["Crop Recommendation"])
logger = logging.getLogger(__name__)


async def _open_meteo_live_weather(lat: float, lon: float) -> dict:
    """Use the existing keyless provider when OpenWeatherMap is unavailable."""
    try:
        current = await get_current_weather(lat, lon)
    except (httpx.HTTPError, ValueError) as exc:
        logger.error("Open-Meteo fallback failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="Weather data is currently unavailable.",
        ) from exc

    return {
        "temperature": round(current["temperature"], 1),
        "humidity": round(current["humidity"], 1),
        "rainfall": round(current["precipitation"], 2),
        "description": current["weather_description"],
        "city": current["location_name"],
        "source": "open-meteo",
    }


# ── Recommendation ────────────────────────────────────────────────────────────

@router.post("/recommend")
async def recommend(data: CropRecommendationRequest, user=Depends(get_current_user)):
    """
    Run the crop recommendation model against the supplied soil & climate parameters.
    Persists the result to MongoDB and returns top-3 crop suggestions.
    """
    return await recommend_crop(data.model_dump(), str(user["_id"]))


# ── Live weather auto-fill ────────────────────────────────────────────────────

@router.get("/live-weather")
async def live_weather(
    lat: float = Query(..., ge=-90, le=90,   description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    _user=Depends(get_current_user),  # require authentication
):
    """
    Fetch current weather from OpenWeatherMap for the given coordinates.

    Returns:
        temperature  (°C)
        humidity     (%)
        rainfall     (mm — precipitation last 1 hour, or 0 if no rain)
        description  (text, e.g. "light rain")
        city         (reverse-geocoded city name)

    Uses OpenWeatherMap when its key is valid and falls back to Open-Meteo
    when the key is absent or rejected.
    """
    api_key = settings.OPENWEATHER_API_KEY.strip()
    if not api_key:
        return await _open_meteo_live_weather(lat, lon)

    url = f"{settings.OPENWEATHER_BASE}/weather"
    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": api_key,
        "units": "metric",   # temperature in °C
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            logger.warning("OpenWeatherMap rejected its configured key; using Open-Meteo.")
            return await _open_meteo_live_weather(lat, lon)
        logger.warning("OpenWeatherMap returned HTTP %s.", exc.response.status_code)
        raise HTTPException(
            status_code=502,
            detail=f"OpenWeatherMap is unavailable (HTTP {exc.response.status_code}).",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("OpenWeatherMap request failed (%s)", type(exc).__name__)
        raise HTTPException(status_code=502, detail="OpenWeatherMap request failed.") from exc
    except ValueError as exc:
        logger.error("OpenWeatherMap returned invalid JSON.")
        raise HTTPException(status_code=502, detail="OpenWeatherMap returned an invalid response.") from exc

    # Extract fields (rain is optional — only present when it is actually raining)
    main     = data.get("main", {})
    rain     = data.get("rain", {})
    weather  = data.get("weather") or [{}]
    city     = data.get("name", f"{lat:.2f}, {lon:.2f}")

    return {
        "temperature": round(main.get("temp",     25.0), 1),
        "humidity":    round(main.get("humidity", 70.0), 1),
        "rainfall":    round(rain.get("1h", 0.0),        2),   # mm last hour
        "description": weather[0].get("description", ""),
        "city":        city,
        "source":      "openweathermap",
    }


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history")
async def history(
    page:     int = Query(1,  ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user),
):
    """Return paginated crop recommendation history for the current user."""
    return await get_crop_history(str(user["_id"]), page, per_page)


@router.delete("/history/{record_id}")
async def delete_record(record_id: str, user=Depends(get_current_user)):
    """Delete a single crop recommendation record."""
    deleted = await delete_crop_recommendation(record_id, str(user["_id"]))
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted successfully"}


# ── PDF report ────────────────────────────────────────────────────────────────

@router.get("/report/{record_id}")
async def download_report(record_id: str, user=Depends(get_current_user)):
    """Stream a PDF report for a specific crop recommendation record."""
    from app.core.database import get_db
    from bson import ObjectId

    db = get_db()
    record = await db.crop_recommendations.find_one({
        "_id":     ObjectId(record_id),
        "user_id": ObjectId(str(user["_id"])),
    })
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    record["id"] = str(record["_id"])
    pdf_bytes = generate_crop_report(record, user)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=crop_report_{record_id}.pdf"},
    )
