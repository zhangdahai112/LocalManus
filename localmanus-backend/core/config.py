import os
from dotenv import load_dotenv

load_dotenv()

# Model configurations for AgentScope
# You can add more configurations here
AGENT_MODEL_CONFIGS = [
    {
        "config_name": "local_model",
        "model_type": "openai_chat",
        "model_name": os.getenv("MODEL_NAME", "gpt-4"),
        "api_key": os.getenv("OPENAI_API_KEY", "EMPTY"),
        "base_url": os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
    }
]

# Server configurations
HOST = "0.0.0.0"
PORT = 8000
