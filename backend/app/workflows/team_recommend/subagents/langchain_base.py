"""
LangChain基础Agent - 支持function calling

使用Qwen模型 + LangChain框架实现工具调用
"""
from typing import List
from loguru import logger
from config.settings import settings

try:
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import PromptTemplate
    from langchain_community.chat_models import ChatTongyi
    from langchain.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain not available: {e}")
    LANGCHAIN_AVAILABLE = False
    BaseTool = object  # 占位符


class LangChainAgent:
    """基于LangChain的智能体基类"""

    def __init__(self, name: str, system_prompt: str, tools: List):
        """
        初始化LangChain Agent

        Args:
            name: Agent名称
            system_prompt: 系统提示词
            tools: 工具列表
        """
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.llm = None
        self.agent_executor = None

        if not LANGCHAIN_AVAILABLE:
            logger.warning(f"[{self.name}] LangChain not available, will use fallback mode")
            return

        # 初始化Qwen模型（支持function calling）
        try:
            self.llm = ChatTongyi(
                model_name="qwen-max",  # 或 qwen-plus
                dashscope_api_key=settings.DASHSCOPE_API_KEY,
                temperature=0.7
            )
            logger.info(f"[{self.name}] Using Qwen model with function calling")
        except Exception as e:
            logger.warning(f"[{self.name}] ChatTongyi initialization failed: {e}")
            self.llm = None
            return

        # 创建ReAct prompt模板
        template = """你是一个智能助手，可以使用以下工具：

{tools}

工具名称: {tool_names}

{system_prompt}

请使用以下格式回答：

Question: 用户的问题
Thought: 你需要思考该做什么
Action: 要使用的工具，应该是 [{tool_names}] 中的一个
Action Input: 工具的输入参数
Observation: 工具返回的结果
... (可以重复 Thought/Action/Action Input/Observation 多次)
Thought: 我现在知道最终答案了
Final Answer: 对用户问题的最终回答

开始！

Question: {input}
Thought: {agent_scratchpad}"""

        self.prompt = PromptTemplate.from_template(template).partial(
            system_prompt=system_prompt
        )

        # 创建agent
        try:
            agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=self.prompt
            )

            # 创建executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=5,
                early_stopping_method="generate",
                handle_parsing_errors=True
            )

            logger.info(f"[{self.name}] LangChain Agent initialized with {len(tools)} tools")
        except Exception as e:
            logger.error(f"[{self.name}] Agent creation failed: {e}")
            import traceback
            traceback.print_exc()
            self.agent_executor = None

    async def execute(self, task: str) -> str:
        """
        执行任务

        Args:
            task: 任务描述

        Returns:
            执行结果
        """
        logger.info(f"[{self.name}] Executing task: {task[:100]}...")

        # 如果LangChain agent不可用，回退到直接调用工具
        if not self.agent_executor:
            logger.warning(f"[{self.name}] Agent executor not available, using fallback mode")
            return await self._fallback_execute(task)

        try:
            result = await self.agent_executor.ainvoke({
                "input": task
            })

            output = result.get("output", "")
            logger.success(f"[{self.name}] Task completed")

            return output

        except Exception as e:
            logger.error(f"[{self.name}] Execution failed: {e}")
            import traceback
            traceback.print_exc()

            # 尝试回退模式
            logger.info(f"[{self.name}] Trying fallback mode...")
            return await self._fallback_execute(task)

    async def _fallback_execute(self, task: str) -> str:
        """
        回退执行模式（直接调用工具，不使用LLM决策）

        Args:
            task: 任务描述

        Returns:
            执行结果
        """
        logger.info(f"[{self.name}] Executing in fallback mode")

        try:
            # 简单策略：调用第一个工具
            if self.tools and len(self.tools) > 0:
                tool = self.tools[0]
                logger.info(f"[{self.name}] Calling tool: {tool.name}")

                # 调用工具
                result = await tool.ainvoke(task)

                return f"工具调用结果：\n{result}"
            else:
                return "没有可用的工具"

        except Exception as e:
            logger.error(f"[{self.name}] Fallback execution failed: {e}")
            return f"执行失败: {str(e)}"
