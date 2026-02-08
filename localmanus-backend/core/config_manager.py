import os
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv, set_key

class ConfigManager:
    """Manages system configuration and .env persistence."""
    
    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)
        if not self.env_path.exists():
            self.env_path.touch()
        load_dotenv(self.env_path)

    def get_config(self) -> Dict[str, Any]:
        """Returns the current relevant configuration from environment variables."""
        return {
            "MODEL_NAME": os.getenv("MODEL_NAME", "gpt-4"),
            "OPENAI_API_KEY": self._mask_key(os.getenv("OPENAI_API_KEY", "")),
            "OPENAI_API_BASE": os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1"),
            "AGENT_MEMORY_LIMIT": os.getenv("AGENT_MEMORY_LIMIT", "40"),
            "UPLOAD_SIZE_LIMIT": os.getenv("UPLOAD_SIZE_LIMIT", "10485760"),  # 10MB default
        }

    def update_config(self, new_config: Dict[str, str]) -> bool:
        """Persists new configuration keys to the .env file."""
        try:
            # Only allow specific keys to be updated for security
            allowed_keys = [
                "MODEL_NAME", 
                "OPENAI_API_KEY", 
                "OPENAI_API_BASE", 
                "AGENT_MEMORY_LIMIT",
                "UPLOAD_SIZE_LIMIT"
            ]
            
            for key, value in new_config.items():
                if key in allowed_keys:
                    # Don't update if it's a masked key and hasn't been changed
                    if key == "OPENAI_API_KEY" and value.startswith("sk-...") and len(value) < 15:
                        continue
                    
                    set_key(str(self.env_path), key, value)
            
            # Reload environment variables after update
            load_dotenv(self.env_path, override=True)
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def _mask_key(self, key: str) -> str:
        """Masks sensitive keys for transmission to frontend."""
        if not key or len(key) < 8:
            return key
        return f"{key[:4]}...{key[-4:]}"
