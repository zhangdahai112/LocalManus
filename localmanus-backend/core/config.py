import os
from dotenv import load_dotenv

load_dotenv()

# Model configurations for AgentScope
# You can add more configurations here
AGENT_MODEL_CONFIGS = [
    {
        "config_name": "local_model",
        "model_type": "openai_chat",
        "model_name": os.getenv("MODEL_NAME", "kimi-k2-turbo-preview"),
        "api_key": os.getenv("OPENAI_API_KEY", "sk-XG0oRiSi37C1HAVGUzMax4ZXf3FgaqbvZe5qz58nSRnyWgxV"),
        "base_url": os.getenv("OPENAI_API_BASE", "https://api.moonshot.cn/v1"),
    }
]

# Server configurations
HOST = "0.0.0.0"
PORT = 8000
