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
    """Synchronous wrapper for web_search. Compatible with Streamlit's event loop."""
    try:
        # If there's already a running event loop (e.g. Streamlit), use a new thread
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're inside an existing event loop (Streamlit) — run in a new thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, web_search(query, max_results))
            return future.result(timeout=15)
    else:
        return asyncio.run(web_search(query, max_results))
