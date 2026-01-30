from agentscope.agents import DialogAgent
from agentscope.message import Msg
from core.prompts import MANAGER_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT
import json

class ManagerAgent:
    """
    Standardizes user input and maintains session TraceID.
    As per architecture section 2.1
    """
    def __init__(self, model_config_name: str):
        self.agent = DialogAgent(
            name="Manager",
            sys_prompt=MANAGER_SYSTEM_PROMPT,
            model_config_name=model_config_name
        )

    def process_input(self, user_input: str):
        msg = Msg(name="User", content=user_input, role="user")
        response = self.agent(msg)
        # Attempt to parse JSON if needed, or return raw message
        return response

class PlannerAgent:
    """
    Generates dynamic task Directed Acyclic Graph (DAG) and retrieves tools.
    As per architecture section 2.1
    """
    def __init__(self, model_config_name: str):
        self.agent = DialogAgent(
            name="Planner",
            sys_prompt=PLANNER_SYSTEM_PROMPT,
            model_config_name=model_config_name
        )

    def plan(self, analyzed_input: str):
        msg = Msg(name="Manager", content=analyzed_input, role="user")
        response = self.agent(msg)
        return response

