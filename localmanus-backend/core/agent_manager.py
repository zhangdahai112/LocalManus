import agentscope
from core.config import AGENT_MODEL_CONFIGS
from agents.base_agents import ManagerAgent, PlannerAgent

class AgentLifecycleManager:
    def __init__(self):
        # Initialize AgentScope with model configs
        agentscope.init(model_configs=AGENT_MODEL_CONFIGS)
        
        # Initialize our core agents
        self.manager = ManagerAgent(model_config_name="local_model")
        self.planner = PlannerAgent(model_config_name="local_model")

    def get_agents(self):
        return self.manager, self.planner

# Global instance
agent_lifecycle = None

def init_agents():
    global agent_lifecycle
    if agent_lifecycle is None:
        agent_lifecycle = AgentLifecycleManager()
    return agent_lifecycle.get_agents()
