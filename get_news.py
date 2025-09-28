
from livekit.agents import function_tool, RunContext

@function_tool
async def fetch_news(
    context: RunContext,
    topic: str,
    num_articles: int = 3
) -> str:
    """
    Fetch the latest news articles on a given topic using NewsAPI.

    Parameters:
    - topic: The topic to search news for.
    - num_articles: The number of articles to fetch (default is 3).

    Returns:
    - A string summarizing the latest news articles on the topic.
    """
    import requests
    import os

    NEWS_API_KEY = os.getenv("NEWS_API_KEY")
    if not NEWS_API_KEY:
        return "News API key is not configured."

    url = f"https://newsapi.org/v2/everything?q={topic}&pageSize={num_articles}&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            return "Failed to fetch news articles."

        articles = data.get("articles", [])
        if not articles:
            return f"No news articles found for '{topic}'."

        news_summary = f"Here are the latest news articles on '{topic}':\n"
        for i, article in enumerate(articles, start=1):
            title = article.get("title", "No title")
            source = article.get("source", {}).get("name", "Unknown source")
            news_summary += f"{i}. {title} ({source})\n"

        return news_summary.strip()

    except requests.RequestException as e:
        return f"An error occurred while fetching news: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"