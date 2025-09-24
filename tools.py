import logging
from livekit.agents import function_tool, RunContext
import requests
import os
from googleapiclient.discovery import build
from livekit.agents import function_tool, RunContext
from datetime import datetime

# Weather API setup
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # store your API key in .env
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Initialize Google Custom Search API
def google_search_service():
    return build("customsearch", "v1", developerKey=os.getenv("GOOGLE_SEARCH_API_KEY"))

@function_tool()
async def search_web(query: str, context: RunContext) -> str:
    """
    Perform a web search using Google Custom Search API and return the top 3 results.
    """
    service = google_search_service()
    res = service.cse().list(q=query, cx=os.getenv("SEARCH_ENGINE_ID")).execute()

    if 'items' not in res:
        return "Sorry, I couldn't find any relevant information."

    results = res['items'][:3]
    response = "Here are the top results I found:\n"
    for idx, item in enumerate(results, start=1):
        title = item.get("title", "No title")
        link = item.get("link", "No link")
        snippet = item.get("snippet", "No description")
        response += f"{idx}. {title} - {link}\n   {snippet}\n"

    # Log the search results to the console
    print("Search Results:", response)

    return response

@function_tool
async def get_current_datetime(context: RunContext) -> str:
    """
    Get the current date and time in ISO 8601 format
    """

    return datetime.now().isoformat()

@function_tool()
async def get_weather(city: str, context: RunContext) -> str:
    """
    Get current weather for a given city.
    """
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"  # Celsius
    }

    try:
        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()

        if data.get("cod") != 200:
            speak_text = f"Sorry, I couldn't find weather information for {city}."
            print(speak_text)
            return speak_text

        weather_desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]

        speak_text = (
            f"Weather in {city}: {weather_desc}. "
            f"Temperature: {temp}°C, feels like {feels_like}°C. "
            f"Humidity: {humidity}%."
        )

        # Log to console
        print(speak_text)

        # Speak the result
        try:
            await context.agent.say(speak_text)
        except AttributeError:
            # fallback if context.agent not available
            pass

        return speak_text

    except Exception as e:
        error_text = f"Error fetching weather: {e}"
        print(error_text)
        return error_text