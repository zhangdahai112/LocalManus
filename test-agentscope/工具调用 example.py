from pydantic import BaseModel, Field
import json
import agentscope
from agentscope.tool import ToolResponse, Toolkit
from agentscope.message import TextBlock
print(agentscope.__version__)


async def my_search(query: str, api_key: str) -> ToolResponse:
    """
        A simple search tool from agentscope

        Args:
            query (str):
                The query key
            api_key (str):
                the api key for authentication.
    """
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text="This is a test"
            )
        ]
    )

tool_kit = Toolkit()
tool_kit.register_tool_function(my_search)

print("tool jon schema")
# print(json.dumps(tool_kit.get_json_schemas(), indent=4))


# 设置思考

class ThinkModel(BaseModel):
    think: str = Field(..., description="总结当前的状态，思考下一步应该做什么")


tool_kit.set_extended_model("my_search", ThinkModel)

print(json.dumps(tool_kit.get_json_schemas(), indent=4))
