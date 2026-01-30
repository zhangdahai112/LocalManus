from agentscope.agent import ReActAgent
from agentscope.message import Msg
from core.prompts import MANAGER_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT
import json

class ManagerAgent:
    """
    Standardizes user input and maintains session TraceID.
    As per architecture section 2.1
    """
    def __init__(self, model, formatter):
        self.agent = ReActAgent(
            name="Manager",
            sys_prompt=MANAGER_SYSTEM_PROMPT,
            model=model,
            formatter=formatter
        )

    async def process_input(self, user_input: str):
        msg = Msg(name="User", content=user_input, role="user")
        response = await self.agent(msg)
        return response

class PlannerAgent:
    """
    Generates dynamic task Directed Acyclic Graph (DAG) and retrieves tools.
    As per architecture section 2.1
    """
    def __init__(self, model, formatter):
        self.agent = ReActAgent(
            name="Planner",
            sys_prompt=PLANNER_SYSTEM_PROMPT,
            model=model,
            formatter=formatter
        )

    async def plan(self, analyzed_input: str):
        msg = Msg(name="Manager", content=analyzed_input, role="user")
        response = await self.agent(msg)
        return response

