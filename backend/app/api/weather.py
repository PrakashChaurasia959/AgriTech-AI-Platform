"""Weather API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.deps import get_current_user
from app.services.weather_service import get_weather_forecast, geocode_location

router = APIRouter(prefix="/weather", tags=["Weather Forecast"])


@router.get("/forecast")
async def forecast(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    location: str = Query(""),
    user=Depends(get_current_user),
):
    """Get current weather and 7-day forecast."""
    try:
        return await get_weather_forecast(lat, lon, location)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather service error: {str(exc)}")


@router.get("/current")
async def current(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    location: str = Query(""),
    user=Depends(get_current_user),
):
    """Get current weather only."""
    from app.services.weather_service import get_current_weather
    try:
        return await get_current_weather(lat, lon, location)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Weather service error: {str(exc)}")


@router.get("/geocode")
async def geocode(
    q: str = Query(..., min_length=2),
    user=Depends(get_current_user),
):
    """Geocode a location name to coordinates."""
    result = await geocode_location(q)
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return result
