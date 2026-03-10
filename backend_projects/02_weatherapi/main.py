import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Weather API", description="Get current weather for any city")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


class WeatherResponse(BaseModel):
    city: str
    country: str
    latitude: float
    longitude: float
    temperature_c: float
    feels_like_c: float
    humidity_percent: int
    wind_speed_kmh: float
    wind_direction_deg: int
    condition: str
    is_day: bool


async def geocode(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(GEOCODING_URL, params={"name": city, "count": 1, "language": "en", "format": "json"})
        response.raise_for_status()
        data = response.json()

    results = data.get("results")
    if not results:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    return results[0]


async def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "weather_code",
            "is_day",
        ],
        "wind_speed_unit": "kmh",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(WEATHER_URL, params=params)
        response.raise_for_status()
        return response.json()


@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str = Query(..., description="Name of the city")):
    location = await geocode(city)
    weather = await fetch_weather(location["latitude"], location["longitude"])

    current = weather["current"]
    code = current["weather_code"]

    return WeatherResponse(
        city=location["name"],
        country=location.get("country", "Unknown"),
        latitude=location["latitude"],
        longitude=location["longitude"],
        temperature_c=current["temperature_2m"],
        feels_like_c=current["apparent_temperature"],
        humidity_percent=current["relative_humidity_2m"],
        wind_speed_kmh=current["wind_speed_10m"],
        wind_direction_deg=current["wind_direction_10m"],
        condition=WMO_CODES.get(code, f"Unknown (code {code})"),
        is_day=bool(current["is_day"]),
    )


@app.get("/")
async def root():
    return {"message": "Weather API is running. Use GET /weather?city=<city_name>"}
