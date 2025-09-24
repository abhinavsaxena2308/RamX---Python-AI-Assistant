import logging
from livekit.agents import function_tool, RunContext
import requests
import os
from googleapiclient.discovery import build
from livekit.agents import function_tool, RunContext
from datetime import datetime

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