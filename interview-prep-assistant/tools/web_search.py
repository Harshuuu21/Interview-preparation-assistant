import httpx
import os
import asyncio

async def web_search(query: str, num_results: int = 5) -> list[dict]:
    """Search the web using Serper API."""
    api_key = os.getenv("SERPER_API_KEY")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num_results},
            timeout=10.0
        )
        data = response.json()
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", "")
            })
        return results

def perform_search(query: str, max_results: int = 5) -> list[dict]:
    """Synchronous wrapper for web_search since our celery tasks are synchronous."""
    # Run the async web_search synchronously
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(web_search(query, max_results))
