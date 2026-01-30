import os
import subprocess
import logging
import uuid
import shutil
from typing import Dict, Any, List

logger = logging.getLogger("LocalManus-Sandbox")

class SandboxManager:
    """
    Manages isolated environments for project generation and code execution.
    In a real-world scenario, this would interface with Docker or Firecracker.
    For local development, we'll use unique directories.
    """
    BASE_SANDBOX_DIR = "sandboxes"

    def __init__(self):
        if not os.path.exists(self.BASE_SANDBOX_DIR):
            os.makedirs(self.BASE_SANDBOX_DIR)

    def create_sandbox(self, user_id: str) -> str:
        """
        Creates a dedicated sandbox directory for a user.
        """
        sandbox_path = os.path.join(self.BASE_SANDBOX_DIR, str(user_id))
        if not os.path.exists(sandbox_path):
            os.makedirs(sandbox_path)
            logger.info(f"Created sandbox for user {user_id} at {sandbox_path}")
        return os.path.abspath(sandbox_path)

    def execute_command(self, user_id: str, command: str, cwd: str = None) -> Dict[str, Any]:
        """
        Executes a command inside the user's sandbox.
        """
        sandbox_path = self.create_sandbox(user_id)
        execution_cwd = cwd if cwd else sandbox_path
        
        # Ensure execution_cwd is within sandbox_path for security
        if not os.path.abspath(execution_cwd).startswith(os.path.abspath(sandbox_path)):
             execution_cwd = sandbox_path

        try:
            logger.info(f"Executing command in sandbox {user_id}: {command}")
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=execution_cwd,
                text=True
            )
            stdout, stderr = process.communicate(timeout=300) # 5 min timeout
            
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out after 5 minutes.",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "exit_code": -1
            }

# Global Instance
sandbox_manager = SandboxManager()
