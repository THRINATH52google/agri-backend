# app/agents/tools/weather.py
import os

import requests
from datetime import datetime


def get_weather_forecast(location: str) -> str:
    """Get current and 3-day forecast for a location (village, district)."""
    if not location or location.strip() == "":
        return "❌ Please provide a location (city, village, or district) to get weather information."

    try:
        # Public API (you may replace with OpenWeatherMap or IMD APIs)
        WEATHER_API_URL = "https://api.weatherapi.com/v1/forecast.json"
        API_KEY = ""

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
            return f"❌ Weather API Error: {data['error']['message']}. Please check the location name."

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
        return f"❌ Failed to get weather for {location}: {str(e)}"
