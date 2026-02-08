from core.skill_manager import BaseSkill
from agentscope.tool import execute_python_code, execute_shell_command, ToolResponse
import asyncio


class SystemExecutionSkill(BaseSkill):
    """
    Standardized skill for system operations including code execution and shell commands.
    """

    def __init__(self):
        super().__init__()
        self.name = "system_execution"
        self.description = "Skill for system operations including code execution and shell commands."

    async def python_execute(self, code: str) -> ToolResponse:
        """
        Executes Python code and returns the output. 
        Note: You must use 'print()' to see output.

        Args:
            code (str): The Python code to execute

        Returns:
            ToolResponse: Output of the executed code or error message
        """
        response = await execute_python_code(code)
        return response

    async def shell_execute(self, command: str) -> ToolResponse:
        """
        Executes a shell command and returns the result.

        Args:
            command (str): The shell command to execute

        Returns:
            ToolResponse: Result of the executed command or error message
        """
        response = await execute_shell_command(command)
        return response


class SystemTools(BaseSkill):
    """
    Legacy class maintained for backward compatibility.
    Use SystemExecutionSkill instead.
    """
    
    def __init__(self):
        super().__init__()
        self.system_execution_skill = SystemExecutionSkill()

    async def run_python(self, code: str) -> ToolResponse:
        """
        Executes Python code and returns the output. 
        Note: You must use 'print()' to see output.
        
        Args:
            code (str): The Python code to execute
        
        Returns:
            ToolResponse: Output of the executed code or error message
        """
        return await self.system_execution_skill.python_execute(code)

    async def run_shell(self, command: str) -> ToolResponse:
        """
        Executes a shell command and returns the result.
        
        Args:
            command (str): The shell command to execute
        
        Returns:
            ToolResponse: Result of the executed command or error message
        """
        return await self.system_execution_skill.shell_execute(command)
