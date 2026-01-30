import asyncio
import inspect
import json
from typing import Any, AsyncGenerator

from pydantic import BaseModel, Field

import agentscope
from agentscope.message import TextBlock, ToolUseBlock
from agentscope.tool import ToolResponse, Toolkit
async def non_streaming_function() -> ToolResponse:
    """A non-streaming tool function that can be interrupted."""
    await asyncio.sleep(1)  # Simulate a long-running task

    # Fake interruption for demonstration
    raise asyncio.CancelledError()

    # The following code won't be executed due to the cancellation
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text="Run successfully!",
            ),
        ],
    )


async def example_tool_interruption() -> None:
    """Example of tool interruption."""
    toolkit = Toolkit()
    toolkit.register_tool_function(non_streaming_function)
    res = await toolkit.call_tool_function(
        ToolUseBlock(
            type="tool_use",
            id="123",
            name="non_streaming_function",
            input={},
        ),
    )

    async for tool_response in res:
        print("Tool Response:")
        print(tool_response)
        print("The interrupted flag:")
        print(tool_response.is_interrupted)


asyncio.run(example_tool_interruption())