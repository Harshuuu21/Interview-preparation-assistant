from duckduckgo_search import DDGS
from typing import List, Dict, Any

def perform_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Performs a web search using duckduckgo_search.
    Returns a list of dicts with 'title', 'href', and 'body' keys.
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
    except Exception as e:
        print(f"Search failed for query '{query}': {e}")
    return results
