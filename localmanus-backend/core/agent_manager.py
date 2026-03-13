import agentscope
import os
from agentscope.model import OpenAIChatModel
from core.moonshot_formatter import MoonshotChatFormatter
from agentscope.memory import InMemoryMemory
from agents.base_agents import ManagerAgent, PlannerAgent
from agents.react_agent import ReActAgent
from core.skill_manager import SkillManager
from core.config import AGENT_MODEL_CONFIGS

class AgentLifecycleManager:
    def __init__(self):
        # Initialize AgentScope
        agentscope.init()
       
        # Get model configuration from AGENT_MODEL_CONFIGS
        model_config = AGENT_MODEL_CONFIGS[0] if AGENT_MODEL_CONFIGS else {}
        
        # Instantiate model using config (with env var fallbacks)
        # Note: extra_body for reasoning_split is not directly supported by AgentScope's
        # OpenAIChatModel. If thinking mode causes issues, use a model without thinking.
        self.model = OpenAIChatModel(
            model_name=model_config.get("model_name", os.getenv("MODEL_NAME", "gpt-4")),
            api_key=model_config.get("api_key", os.getenv("OPENAI_API_KEY", "EMPTY")),
            stream=True,
            client_kwargs={"base_url": model_config.get("base_url", os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"))},
        )
        
        # Use Moonshot-compatible formatter that preserves reasoning_content
        # for thinking-enabled models (e.g., Moonshot/Kimi)
        self.formatter = MoonshotChatFormatter()
        
        # Initialize skill manager
        self.skill_manager = SkillManager()
        
        # Initialize our core agents with the model instance and other requirements
        self.manager = ManagerAgent(model=self.model, formatter=self.formatter)
        self.planner = PlannerAgent(model=self.model, formatter=self.formatter)
        
        # Memory compression settings (configurable via environment variables)
        enable_compression = os.getenv("ENABLE_MEMORY_COMPRESSION", "true").lower() == "true"
        compression_threshold = int(os.getenv("MEMORY_COMPRESSION_THRESHOLD", "10000"))
        keep_recent = int(os.getenv("MEMORY_KEEP_RECENT", "3"))
        
        self.react_agent = ReActAgent(
            model=self.model, 
            formatter=self.formatter, 
            skill_manager=self.skill_manager,
            enable_compression=enable_compression,
            compression_threshold=compression_threshold,
            keep_recent=keep_recent,
        )

    def get_agents(self):
        return self.manager, self.planner, self.react_agent

# Global instance
agent_lifecycle = None

def init_agents():
    global agent_lifecycle
    if agent_lifecycle is None:
        agent_lifecycle = AgentLifecycleManager()
    return agent_lifecycle.get_agents()
