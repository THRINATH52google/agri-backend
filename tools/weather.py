# app/agents/tools/weather.py

import requests
from datetime import datetime
from langchain.tools import tool

# Public API (you may replace with OpenWeatherMap or IMD APIs)
WEATHER_API_URL = "https://api.weatherapi.com/v1/forecast.json"
API_KEY = ""
@tool
def get_weather_forecast(location: str) -> str:
    """Get current and 3-day forecast for a location (village, district)."""
    try:
        response = requests.get(
            WEATHER_API_URL,
            params={
                "key": API_KEY,
                "q": location,
                "days": 3,
                "aqi": "no",
                "alerts": "no"
            }
        )
        data = response.json()
        if "error" in data:
            return f"Error: {data['error']['message']}"

        forecast_data = data["forecast"]["forecastday"]
        result = f"🌦️ Weather Forecast for {location}:\n"

        for day in forecast_data:
            date = day["date"]
            condition = day["day"]["condition"]["text"]
            min_temp = day["day"]["mintemp_c"]
            max_temp = day["day"]["maxtemp_c"]
            rain_chance = day["day"]["daily_chance_of_rain"]

            result += (
                f"\n📅 {date}:\n"
                f" - Condition: {condition}\n"
                f" - Temp: {min_temp}°C to {max_temp}°C\n"
                f" - 🌧️ Rain chance: {rain_chance}%\n"
            )

        return result

    except Exception as e:
        return f"Failed to get weather: {str(e)}"
