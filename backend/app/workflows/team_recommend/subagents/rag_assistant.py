"""
RAG Assistant - 基于LangChain + Function Calling

使用Milvus混合检索工具
"""
from .langchain_base import LangChainAgent
from .rag_tools import search_travel_knowledge
from loguru import logger
from typing import List, Dict, Any


class RAGAssistant(LangChainAgent):
    """RAG知识库助手 - 使用LangChain + tools"""

    def __init__(self):
        tools = [
            search_travel_knowledge
        ]

        system_prompt = """你是一个旅游知识库助手，负责从知识库中检索相关信息。

你有以下工具可用：
- search_travel_knowledge(query, entities) - 从Milvus向量库搜索旅游信息

**工作流程：**
1. 理解用户查询
2. 使用 search_travel_knowledge 工具搜索相关信息
3. 整合结果，以友好的方式返回给用户

**返回格式：**
- 如果找到结果，列出景点名称、描述、类别
- 如果没有找到，礼貌告知用户
- 保持回答简洁专业，突出重点信息"""

        super().__init__(
            name="RAG知识库助手",
            system_prompt=system_prompt,
            tools=tools
        )

        logger.info("[RAG Assistant] Initialized with LangChain + function calling")

    async def search(self, query: str, entities: List[str] = None) -> Dict[str, Any]:
        """
        便捷方法：直接调用搜索工具

        Args:
            query: 查询文本
            entities: 实体列表

        Returns:
            搜索结果
        """
        try:
            # 直接调用工具
            result_json = await search_travel_knowledge.ainvoke({
                "query": query,
                "entities": entities
            })

            import json
            result = json.loads(result_json)

            return result

        except Exception as e:
            logger.error(f"[RAG Assistant] Search failed: {e}")
            return {
                "success": False,
                "found": 0,
                "error": str(e)
            }

