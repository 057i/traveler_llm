"""Tavily Client"""
from typing import List, Dict, Any
from loguru import logger


class TavilyClient:
    """
    Tavily搜索客户端 - 网络搜索服务

    功能：
    - 调用Tavily API进行网络搜索
    - 支持深度搜索模式（advanced）
    - 返回标题、URL、内容和相关性分数

    使用场景：
    - 当本地知识库检索置信度不足时触发
    - 补充最新的旅游信息
    - 提供权威网络来源
    """

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
        使用Tavily API进行网络搜索

        Args:
            query: 搜索查询词
            max_results: 最多返回结果数（默认3条）

        Returns:
            搜索结果列表，每项包含：
            - title: 网页标题
            - url: 网页链接
            - content: 网页摘要内容
            - score: 相关性分数

        示例：
            >>> client = TavilyClient()
            >>> results = client.search("北京旅游攻略", max_results=5)
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
