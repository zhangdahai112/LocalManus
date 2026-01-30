import agentscope
import os
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agents.base_agents import ManagerAgent, PlannerAgent
from agents.react_agent import ReActAgent
from core.skill_manager import SkillManager

class AgentLifecycleManager:
    def __init__(self):
        # Initialize AgentScope
        agentscope.init()
       
        # Instantiate model directly for AgentScope 1.0
        self.model = OpenAIChatModel(
            model_name=os.getenv("MODEL_NAME", "gpt-4"),
            api_key=os.getenv("OPENAI_API_KEY", "EMPTY"),
            streaming=True,
            client_kwargs={"base_url": os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1")},
        )
        
        # Instantiate formatters and memory for AgentScope 1.0
        self.formatter = OpenAIChatFormatter()
        
        # Initialize skill manager
        self.skill_manager = SkillManager()
        
        # Initialize our core agents with the model instance and other requirements
        self.manager = ManagerAgent(model=self.model, formatter=self.formatter)
        self.planner = PlannerAgent(model=self.model, formatter=self.formatter)
        self.react_agent = ReActAgent(model=self.model, formatter=self.formatter, skill_manager=self.skill_manager)

    def get_agents(self):
        return self.manager, self.planner, self.react_agent

# Global instance
agent_lifecycle = None

def init_agents():
    global agent_lifecycle
    if agent_lifecycle is None:
        agent_lifecycle = AgentLifecycleManager()
    return agent_lifecycle.get_agents()
