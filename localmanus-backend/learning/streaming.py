import asyncio
import os
from agentscope.agent import ReActAgent
from agentscope.tool import Toolkit, ToolResponse
from agentscope.model import OpenAIChatModel
from agentscope.memory import InMemoryMemory
from agentscope.tool import execute_python_code
from agentscope.formatter import DashScopeChatFormatter
from agentscope.message import Msg


async def creating_react_agent() -> None:
    """Create a ReAct agent and run a simple task."""
    # Prepare tools
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)

    jarvis = ReActAgent(
        name="Jarvis",
        sys_prompt="You're a helpful assistant named Jarvis",
        model=OpenAIChatModel(
            client_kwargs={"base_url": "https://api.deepseek.com/v1"},
            model_name="deepseek-chat",
            api_key="sk-81011e20abcf42cab8f7ecdb48e08857",
            stream=True
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    msg = Msg(
        name="user",
        content="Hi! Jarvis, run Hello World in Python.",
        role="user",
    )

    await jarvis(msg)


asyncio.run(creating_react_agent())