import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import subprocess
import time
import pyautogui
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
        
    
@function_tool()
async def web_search(query: str) -> str:
    """
    Perform a web search using DuckDuckGo and return the top results.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Web search results '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error performing web search: {e}")
        return "Sorry, I couldn't perform the web search at the moment."

@function_tool()
async def get_current_date_time() -> str:
    """
    Get the current date and time.
    """
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Current date and time: {current_time}")
    return current_time


