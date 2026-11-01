"""Weather Pydantic schemas."""
from pydantic import BaseModel


class WeatherRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_name: str = ""


class CurrentWeather(BaseModel):
    temperature: float
    apparent_temperature: float
    humidity: float
    wind_speed: float
    precipitation: float
    weather_code: int
    weather_description: str
    cloud_cover: float
    location_name: str
    farming_advice: str


class ForecastDay(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    precipitation: float
    weather_code: int
    weather_description: str
    wind_speed_max: float


class WeatherForecast(BaseModel):
    location_name: str
    current: CurrentWeather
    forecast: list[ForecastDay]
    farming_advice: str


from pydantic import Field
