"""
Crop recommendation API routes.

Extra endpoint added:
  GET /api/crop/live-weather
    Accepts lat/lon, returns OpenWeatherMap current weather
    (temperature, humidity, precipitation in mm).
    Used by the frontend to auto-fill the climate sliders.
    Returns 501 if OPENWEATHER_API_KEY is not configured.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.deps import get_current_user
from app.schemas.crop import CropRecommendationRequest
from app.services.crop_service import recommend_crop, get_crop_history, delete_crop_recommendation
from app.services.report_service import generate_crop_report

router = APIRouter(prefix="/crop", tags=["Crop Recommendation"])


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

    Requires OPENWEATHER_API_KEY to be set in .env.
    Returns HTTP 501 if the key is absent.
    Returns HTTP 502 if the upstream API call fails.
    """
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=501,
            detail=(
                "Live weather is not configured. "
                "Set OPENWEATHER_API_KEY in .env to enable this feature.  "
                "Get a free key at https://openweathermap.org/api"
            ),
        )

    import httpx

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
        raise HTTPException(
            status_code=502,
            detail=f"OpenWeatherMap returned {exc.response.status_code}: {exc.response.text[:200]}",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather fetch error: {exc}")

    # Extract fields (rain is optional — only present when it is actually raining)
    main     = data.get("main", {})
    rain     = data.get("rain", {})
    weather  = data.get("weather", [{}])
    city     = data.get("name", f"{lat:.2f}, {lon:.2f}")

    return {
        "temperature": round(main.get("temp",     25.0), 1),
        "humidity":    round(main.get("humidity", 70.0), 1),
        "rainfall":    round(rain.get("1h", 0.0),        2),   # mm last hour
        "description": weather[0].get("description", ""),
        "city":        city,
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
