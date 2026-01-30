import importlib
import inspect
import os
from typing import Dict, Any, List

class BaseSkill:
    """
    Base class for all skills. 
    Each skill should implement a 'route' method to dispatch tools.
    """
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "No description provided."

    async def execute(self, tool_name: str, **kwargs) -> Any:
        """
        Routes the request to the appropriate tool method.
        """
        method = getattr(self, tool_name, None)
        if method and callable(method):
            if inspect.iscoroutinefunction(method):
                return await method(**kwargs)
            else:
                return method(**kwargs)
        raise ValueError(f"Tool '{tool_name}' not found in skill '{self.name}'")

    def get_tools_metadata(self) -> List[Dict[str, Any]]:
        """
        Returns metadata for all available tools in this skill.
        Used by the Agent to understand what it can do.
        """
        tools = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not name.startswith('_') and name not in ['execute', 'get_tools_metadata']:
                tools.append({
                    "name": name,
                    "description": method.__doc__ or "No tool description.",
                    "parameters": str(inspect.signature(method))
                })
        return tools

class SkillManager:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, BaseSkill] = {}
        self._load_skills()

    def _load_skills(self):
        """
        Dynamically loads all skills from the skills directory.
        """
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            
        # Add the current directory to sys.path for absolute imports if needed
        import sys
        if os.getcwd() not in sys.path:
            sys.path.append(os.getcwd())

        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"skills.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                            skill_instance = obj()
                            self.skills[skill_instance.name.lower()] = skill_instance
                except Exception as e:
                    print(f"Failed to load skill from {filename}: {e}")

    def get_skill(self, name: str) -> BaseSkill:
        return self.skills.get(name.lower())

    def list_all_tools(self) -> List[Dict[str, Any]]:
        all_tools = []
        for skill_name, skill in self.skills.items():
            for tool in skill.get_tools_metadata():
                all_tools.append({
                    "skill": skill_name,
                    **tool
                })
        return all_tools
