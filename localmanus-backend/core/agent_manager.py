import agentscope
from core.config import AGENT_MODEL_CONFIGS
from agents.base_agents import ManagerAgent, PlannerAgent
from agents.react_agent import ReActAgent
from core.skill_manager import SkillManager

class AgentLifecycleManager:
    def __init__(self):
        # Initialize AgentScope with model configs
        agentscope.init(model_configs=AGENT_MODEL_CONFIGS)
        
        # Initialize skill manager
        self.skill_manager = SkillManager()
        
        # Initialize our core agents
        self.manager = ManagerAgent(model_config_name="local_model")
        self.planner = PlannerAgent(model_config_name="local_model")
        self.react_agent = ReActAgent(model_config_name="local_model", skill_manager=self.skill_manager)

    def get_agents(self):
        return self.manager, self.planner, self.react_agent

# Global instance
agent_lifecycle = None

def init_agents():
    global agent_lifecycle
    if agent_lifecycle is None:
        agent_lifecycle = AgentLifecycleManager()
    return agent_lifecycle.get_agents()
