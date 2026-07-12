"""Tavily Client"""
from typing import List, Dict, Any
from loguru import logger


class TavilyClient:
    """Tavily search client"""

    def __init__(self):
        """Initialize Tavily client"""
        from config.settings import settings
        self.api_key = settings.TAVILY_API_KEY

    def search(
        self,
        query: str,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search using Tavily API

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Search results
        """
        if not self.api_key:
            logger.warning("[Tavily] API Key not configured")
            return []

        try:
            from tavily import TavilyClient as TavilyAPI

            client = TavilyAPI(api_key=self.api_key)

            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )

            # Format results
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })

            logger.success(f"[Tavily] Found {len(results)} results")
            return results

        except ImportError:
            logger.error("[Tavily] tavily-python not installed")
            return []

        except Exception as e:
            logger.error(f"[Tavily] Search failed: {e}")
            return []


_tavily_client = None


def get_tavily_client() -> TavilyClient:
    """Get singleton Tavily client instance"""
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient()
    return _tavily_client
