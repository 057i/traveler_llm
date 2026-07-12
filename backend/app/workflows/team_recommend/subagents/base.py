"""
Base SubAgent class for team recommendation
"""
from typing import Dict, Any, Optional, List
from loguru import logger
from dashscope import Generation
from config.settings import settings


class BaseSubAgent:
    """Base class for all subagents"""

    def __init__(self, name: str, system_prompt: str):
        """
        Initialize subagent

        Args:
            name: Agent name
            system_prompt: System prompt for the agent
        """
        self.name = name
        self.system_prompt = system_prompt
        self.memory = []

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute task with context

        Args:
            task: Task description
            context: Additional context data

        Returns:
            Task execution result
        """
        logger.info(f"[{self.name}] Executing task: {task[:50]}...")

        prompt = self._build_prompt(task, context)

        try:
            response = Generation.call(
                model=settings.QWEN_MODEL,
                prompt=prompt,
                api_key=settings.DASHSCOPE_API_KEY
            )

            result = response.output.text

            self.memory.append({
                "task": task,
                "result": result
            })

            logger.success(f"[{self.name}] Task completed")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Task failed: {e}")
            raise

    def _build_prompt(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build prompt from task and context

        Args:
            task: Task description
            context: Additional context

        Returns:
            Complete prompt
        """
        prompt = f"""{self.system_prompt}

Task:
{task}
"""

        if context:
            prompt += f"\nContext:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"

        if self.memory:
            prompt += f"\nPrevious interactions:\n"
            for mem in self.memory[-3:]:
                prompt += f"Task: {mem['task']}\nResult: {mem['result'][:200]}...\n\n"

        return prompt

    def clear_memory(self):
        """Clear agent memory"""
        self.memory = []
        logger.info(f"[{self.name}] Memory cleared")
