import importlib
import inspect
import os
import logging
import asyncio
from contextvars import ContextVar
from typing import Dict, Any, List, Optional
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import ToolUseBlock, TextBlock

logger = logging.getLogger("LocalManus-SkillManager")

# Context variable to store user context per async task
# This ensures thread-safety and isolation between concurrent requests
_user_context_var: ContextVar[Optional[Dict]] = ContextVar('user_context', default=None)

class UserContextToolkit(Toolkit):
    """
    Custom Toolkit that injects user_context into tool function calls.
    Uses context variables for async-safe per-request context isolation.
    """
    
    async def call_tool_function(self, tool_block: ToolUseBlock):
        """
        Override to inject user_id/user_context into tool calls.
        Retrieves context from ContextVar for async-safe isolation.
        
        Returns:
            `AsyncGenerator[ToolResponse, None]`: An async generator that yields
            tool response chunks from the parent implementation.
        """
        # Handle both dict and ToolUseBlock object formats
        if isinstance(tool_block, dict):
            tool_name = tool_block.get("name") or tool_block.get("function", {}).get("name", "unknown")
            tool_input = dict(tool_block.get("input", {})) if tool_block.get("input") else {}
            tool_type = tool_block.get("type", "tool_use")
            tool_id = tool_block.get("id", f"tool_{tool_name}")
        else:
            # ToolUseBlock object
            tool_name = getattr(tool_block, "name", "unknown")
            tool_input = dict(getattr(tool_block, "input", {})) if getattr(tool_block, "input", None) else {}
            tool_type = getattr(tool_block, "type", "tool_use")
            tool_id = getattr(tool_block, "id", f"tool_{tool_name}")
        
        if tool_name not in self.tools:
            # Return a list with error response (AgentScope expects a list, not async generator)
            return [ToolResponse(
                content=[TextBlock(
                    type="text",
                    text=f"Error: Tool '{tool_name}' not found."
                )],
                role="tool"
            )]
        
        # Get the original function
        tool_wrapper = self.tools[tool_name]
        original_func = tool_wrapper.original_func
        
        # Check function signature for user_id or user_context parameters
        sig = inspect.signature(original_func)
        
        # Get user context from ContextVar (async-safe)
        user_context = _user_context_var.get()
        
        # Inject user_id if the function accepts it
        if "user_id" in sig.parameters and user_context:
            tool_input["user_id"] = str(user_context.get("id", ""))
        
        # Inject user_context if the function accepts it
        if "user_context" in sig.parameters:
            tool_input["user_context"] = user_context or {}
        
        # Create updated tool block with injected parameters
        updated_block = ToolUseBlock(
            type=tool_type,
            id=tool_id,
            name=tool_name,
            input=tool_input
        )
        
        # AgentScope's _acting method expects a list, not an async generator
        # We need to collect all responses and return them as a list
        gen = await super().call_tool_function(updated_block)
        responses = []
        async for response in gen:
            responses.append(response)
        return responses


class BaseSkill:
    """
    Base class for all skills. 
    Maintained for compatibility with existing skill implementations.
    """
    def __init__(self):
        self.name = self.__class__.__name__

class SkillManager:
    """
    Manager for skills and tools following AgentScope's Toolkit pattern.
    Ref: https://doc.agentscope.io/tutorial/task_agent_skill.html
    """
    def __init__(self, skills_dir: str = "skills"):
        # The skills_dir is relative to the backend root (main.py location)
        self.skills_dir = skills_dir
        self.toolkit = UserContextToolkit()  # Use custom toolkit with user context injection
        self._load_skills()

    def _load_skills(self):
        """
        Scans the skills directory for both Tool Functions (.py files) 
        and Agent Skills (directories with SKILL.md).
        """
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)

        import sys
        import importlib.util
        
        # Ensure the backend root is in path for relative imports within skills
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # 1. Register Agent Skills (Directories with SKILL.md)
        for item in os.listdir(self.skills_dir):
            item_path = os.path.join(self.skills_dir, item)
            if os.path.isdir(item_path):
                skill_md = os.path.join(item_path, "SKILL.md")
                if os.path.exists(skill_md):
                    try:
                        self.toolkit.register_agent_skill(item_path)
                        logger.info(f"Registered Agent Skill: {item}")
                    except Exception as e:
                        logger.error(f"Failed to register agent skill {item}: {e}")

        # 2. Register Tool Functions (.py files)
        for root, _, files in os.walk(self.skills_dir):
            if "__pycache__" in root:
                continue
            for filename in files:
                if filename.endswith(".py") and not filename.startswith("__"):
                    file_path = os.path.join(root, filename)
                    try:
                        # Use importlib.util to load directly from file path
                        # This avoids issues with hyphenated directory names
                        module_name = filename[:-3]
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            for name, obj in inspect.getmembers(module):
                                # Handle classes inheriting from BaseSkill
                                if inspect.isclass(obj) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                                    skill_instance = obj()
                                    for method_name, method in inspect.getmembers(skill_instance, predicate=inspect.ismethod):
                                        if not method_name.startswith("_") and method.__doc__:
                                            self.toolkit.register_tool_function(method)
                                            logger.info(f"Registered tool: {method_name} from {obj.__name__} in {filename}")
                                
                                # Handle standalone functions
                                elif inspect.isfunction(obj) and not name.startswith("_"):
                                    if obj.__doc__:
                                        self.toolkit.register_tool_function(obj)
                                        logger.info(f"Registered tool: {name} from {filename}")
                    except Exception as e:
                        logger.error(f"Failed to load tools from {file_path}: {e}")

    async def execute_tool(self, tool_name: str, user_context: Optional[Dict] = None, **kwargs) -> Any:
        """
        Executes a registered tool function using AgentScope's toolkit.
        """
        try:
            if tool_name not in self.toolkit.tools:
                raise ValueError(f"Tool '{tool_name}' not found.")
            
            # Inject user context if required by the function signature
            tool_func = self.toolkit.tools[tool_name].original_func
            sig = inspect.signature(tool_func)
            
            if "user_id" in sig.parameters and user_context:
                kwargs["user_id"] = str(user_context.get("id", ""))
            if "user_context" in sig.parameters:
                kwargs["user_context"] = user_context

            # Call via toolkit (handles async wrapping and ToolResponse conversion)
            from agentscope.message import ToolUseBlock
            tool_block = ToolUseBlock(
                type="tool_use",
                id=f"tool_{tool_name}",
                name=tool_name,
                input=kwargs
            )
            
            # Collect all responses from the async generator
            # First await to get the generator, then iterate
            responses = []
            gen = await self.toolkit.call_tool_function(tool_block)
            async for response in gen:
                if isinstance(response, ToolResponse):
                    responses.extend(response.content)
                else:
                    responses.append(response)
            
            # Return combined response content
            if len(responses) == 1:
                return responses[0]
            else:
                return responses
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error: {str(e)}"

    def set_user_context(self, user_context: Optional[Dict]):
        """
        Set the current user context for the current async task.
        Uses ContextVar for async-safe isolation between concurrent requests.
        """
        _user_context_var.set(user_context)
        logger.debug(f"Set user context for task: {user_context}")

    def clear_user_context(self):
        """Clear the user context for the current async task."""
        _user_context_var.set(None)
        logger.debug("Cleared user context for task")

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """Compatibility method for existing ReActAgent."""
        return self.toolkit.get_json_schemas()

    def get_skills_prompt(self) -> Optional[str]:
        """Returns the prompt for all registered agent skills."""
        return self.toolkit.get_agent_skill_prompt()
