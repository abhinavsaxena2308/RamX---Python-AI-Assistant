import logging
from livekit.agents import function_tool, RunContext
import requests
import os

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

@function_tool()
async def get_current_weather(
    context: RunContext,
    city: str) -> str:
    """
    Get the current weather for a given city using a weather API.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather data for '{city}': {response.text}")
            return response.text.strip()
        else:
            logging.error(f"Error fetching weather data: {response.status_code}")
            return "Sorry, I couldn't fetch the weather data at the moment."
        
    except Exception as e:
        logging.error(f"Error fetching weather data: {e}")
        return "Sorry, I couldn't fetch the weather data at the moment."