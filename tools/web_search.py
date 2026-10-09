"""DuckDuckGo web search tool for the ReAct Agent."""

from typing import Optional
from langchain_core.tools import tool

# Support either `ddgs` (preferred modern package) or `duckduckgo_search`
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS  # type: ignore


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Searches the live web using DuckDuckGo to retrieve current information.

    Use this tool when you need real-time data, current events, recent news,
    facts, weather, documentation, or facts outside your internal knowledge.

    Args:
        query: The search query string.
        max_results: The maximum number of search results to return (default: 5).

    Returns:
        A formatted string of search results including titles, links, and snippets.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return "Error: Search query cannot be empty."

    try:
        ddgs_client = DDGS()
        results = list(ddgs_client.text(cleaned_query, max_results=max(1, min(max_results, 10))))

        if not results:
            return f"No search results found for query: '{cleaned_query}'"

        formatted = []
        for i, item in enumerate(results, start=1):
            title = item.get("title", "No Title")
            href = item.get("href", "")
            body = item.get("body", "No description available.")
            formatted.append(f"[{i}] {title}\nURL: {href}\nSnippet: {body}\n")

        return "\n".join(formatted)

    except Exception as exc:
        return f"Error executing DuckDuckGo search: {str(exc)}"
