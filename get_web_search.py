import logging
from livekit.agents import function_tool
from langchain_community.tools import DuckDuckGoSearchRun

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