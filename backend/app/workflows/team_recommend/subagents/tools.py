"""
"""
from typing import Dict, Any, List, Callable, Optional
from functools import wraps
import json
from loguru import logger


class AgentTool:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

    async def execute(self, **kwargs) -> Any:

    Args:
    Example:
        @agent_tool(
            name="search_attractions",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                    },
                    "category": {
                        "type": "string",
                    }
                },
                "required": ["location"]
            }
        )
        async def search_attractions(location: str, category: str = None):
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        wrapper._is_agent_tool = True
        wrapper._tool_name = name
        wrapper._tool_description = description
        wrapper._tool_parameters = parameters

        return wrapper

    return decorator


class ToolEnabledAgent:

    def __init__(self):
        self.tools: Dict[str, AgentTool] = {}
        self._register_tools()

    def _register_tools(self):
        return [tool.to_function_definition() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        if not self.tools:
            return ""

        for tool in self.tools.values():
            tools_text += f"\n### {tool.name}\n"

        return tools_text
