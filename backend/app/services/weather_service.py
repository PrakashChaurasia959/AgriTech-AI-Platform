"""Weather service using the free Open-Meteo API (no API key required)."""
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# WMO weather codes mapped to descriptions
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def _weather_description(code: int) -> str:
    return WMO_CODES.get(code, "Unknown")


def _farming_advice(temp: float, humidity: float, precipitation: float, wind_speed: float) -> str:
    """Generate farming advice based on weather conditions."""
    advice_parts = []

    if temp > 35:
        advice_parts.append("High temperature — ensure adequate irrigation and consider shade for sensitive crops.")
    elif temp < 10:
        advice_parts.append("Low temperature — protect crops from cold stress and delay sowing if needed.")
    elif 15 <= temp <= 30:
        advice_parts.append("Optimal temperature for most crop growth.")

    if humidity > 80:
        advice_parts.append("High humidity — monitor for fungal diseases and improve air circulation.")
    elif humidity < 30:
        advice_parts.append("Low humidity — increase irrigation frequency to prevent water stress.")

    if precipitation > 25:
        advice_parts.append("Heavy rainfall expected — ensure proper drainage to avoid waterlogging.")
    elif precipitation < 1 and temp > 25:
        advice_parts.append("Low rainfall with warm temperatures — irrigate crops adequately.")

    if wind_speed > 30:
        advice_parts.append("Strong winds — secure tall crops and delay pesticide application.")

    if not advice_parts:
        advice_parts.append("Weather conditions are favorable for normal farming activities.")

    return " ".join(advice_parts)


async def get_current_weather(latitude: float, longitude: float, location_name: str = "") -> dict:
    """Fetch current weather from Open-Meteo."""
    url = f"{settings.WEATHER_API_BASE}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,precipitation,weather_code,cloud_cover",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    current = data.get("current", {})
    temp = current.get("temperature_2m", 0)
    humidity = current.get("relative_humidity_2m", 0)
    precipitation = current.get("precipitation", 0)
    wind_speed = current.get("wind_speed_10m", 0)
    weather_code = current.get("weather_code", 0)

    return {
        "temperature": temp,
        "apparent_temperature": current.get("apparent_temperature", temp),
        "humidity": humidity,
        "wind_speed": wind_speed,
        "precipitation": precipitation,
        "weather_code": weather_code,
        "weather_description": _weather_description(weather_code),
        "cloud_cover": current.get("cloud_cover", 0),
        "location_name": location_name or f"{latitude:.2f}, {longitude:.2f}",
        "farming_advice": _farming_advice(temp, humidity, precipitation, wind_speed),
    }


async def get_weather_forecast(latitude: float, longitude: float, location_name: str = "") -> dict:
    """Fetch current weather and 7-day forecast from Open-Meteo."""
    url = f"{settings.WEATHER_API_BASE}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,precipitation,weather_code,cloud_cover",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 7,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    temp = current.get("temperature_2m", 0)
    humidity = current.get("relative_humidity_2m", 0)
    precipitation = current.get("precipitation", 0)
    wind_speed = current.get("wind_speed_10m", 0)
    weather_code = current.get("weather_code", 0)

    current_weather = {
        "temperature": temp,
        "apparent_temperature": current.get("apparent_temperature", temp),
        "humidity": humidity,
        "wind_speed": wind_speed,
        "precipitation": precipitation,
        "weather_code": weather_code,
        "weather_description": _weather_description(weather_code),
        "cloud_cover": current.get("cloud_cover", 0),
        "location_name": location_name or f"{latitude:.2f}, {longitude:.2f}",
        "farming_advice": _farming_advice(temp, humidity, precipitation, wind_speed),
    }

    forecast = []
    dates = daily.get("time", [])
    for i in range(min(7, len(dates))):
        code = daily.get("weather_code", [0] * 7)[i] if i < len(daily.get("weather_code", [])) else 0
        forecast.append({
            "date": dates[i],
            "temp_max": daily.get("temperature_2m_max", [0] * 7)[i] if i < len(daily.get("temperature_2m_max", [])) else 0,
            "temp_min": daily.get("temperature_2m_min", [0] * 7)[i] if i < len(daily.get("temperature_2m_min", [])) else 0,
            "precipitation": daily.get("precipitation_sum", [0] * 7)[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "weather_code": code,
            "weather_description": _weather_description(code),
            "wind_speed_max": daily.get("wind_speed_10m_max", [0] * 7)[i] if i < len(daily.get("wind_speed_10m_max", [])) else 0,
        })

    return {
        "location_name": location_name or f"{latitude:.2f}, {longitude:.2f}",
        "current": current_weather,
        "forecast": forecast,
        "farming_advice": _farming_advice(temp, humidity, precipitation, wind_speed),
    }


async def geocode_location(query: str) -> dict | None:
    """Geocode a location name using Open-Meteo's geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": 1, "language": "en", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if results:
                r = results[0]
                return {
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "name": r.get("name", query),
                    "country": r.get("country", ""),
                    "admin1": r.get("admin1", ""),
                }
    except Exception as exc:
        logger.error("Geocoding failed: %s", exc)
    return None
