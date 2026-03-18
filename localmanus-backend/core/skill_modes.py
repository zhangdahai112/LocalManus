"""
Skill Execution Modes for LocalManus

Defines where and how skills should execute:
- HOST: Execute on host machine (API calls, web search)
- SANDBOX: Execute inside user sandbox (file operations, code execution)
- HYBRID: Can work with both (default)
"""

from enum import Enum
from functools import wraps
from typing import Callable, Optional
import logging

logger = logging.getLogger("LocalManus-SkillModes")


class SkillMode(Enum):
    """Skill execution mode"""
    HOST = "host"           # Runs on host machine
    SANDBOX = "sandbox"     # Runs inside sandbox
    HYBRID = "hybrid"       # Can work with both


def skill_mode(mode: SkillMode):
    """
    Decorator to declare a skill's execution mode.
    
    Usage:
        @skill_mode(SkillMode.HOST)
        async def web_search(query: str) -> ToolResponse:
            ...
        
        @skill_mode(SkillMode.SANDBOX)
        async def file_read(path: str, user_id: str) -> ToolResponse:
            ...
    """
    def decorator(func: Callable) -> Callable:
        func._skill_mode = mode
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Mode is just metadata - actual routing handled by skill_manager
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_skill_mode(func: Callable) -> SkillMode:
    """Get the execution mode of a skill function"""
    return getattr(func, '_skill_mode', SkillMode.HYBRID)


# Predefined mode shortcuts
def host_skill(func: Callable) -> Callable:
    """Shortcut for @skill_mode(SkillMode.HOST)"""
    return skill_mode(SkillMode.HOST)(func)


def sandbox_skill(func: Callable) -> Callable:
    """Shortcut for @skill_mode(SkillMode.SANDBOX)"""
    return skill_mode(SkillMode.SANDBOX)(func)


def hybrid_skill(func: Callable) -> Callable:
    """Shortcut for @skill_mode(SkillMode.HYBRID)"""
    return skill_mode(SkillMode.HYBRID)(func)
