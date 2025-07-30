import httpx
from app.core.config import settings

class SearchService:
    def __init__(self):
        self.search_tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information about a topic. Use this when you need recent information or facts that might not be in your training data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to look up information for"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    async def web_search(self, query: str) -> str:
        """Search the web for information about a given query using Google Custom Search API."""
        try:
            if not settings.google_api_key or not settings.google_search_engine_id:
                return "Search unavailable: Google API credentials not configured"
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": settings.google_api_key,
                        "cx": settings.google_search_engine_id,
                        "q": query,
                        "num": 5  # Return top 5 results
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "items" in data and data["items"]:
                        results = []
                        for item in data["items"][:3]:  # Use top 3 results
                            title = item.get("title", "")
                            snippet = item.get("snippet", "")
                            results.append(f"{title}: {snippet}")
                        
                        return f"Search results for '{query}':\n" + "\n\n".join(results)
                    else:
                        return f"No search results found for '{query}'"
                else:
                    return f"Search temporarily unavailable. Status code: {response.status_code}"
                    
        except Exception as e:
            return f"Search error: {str(e)}"

# Global search service instance
search_service = SearchService()