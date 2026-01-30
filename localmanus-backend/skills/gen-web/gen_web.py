from core.skill_manager import BaseSkill
from core.firecracker_sandbox import firecracker_manager
from typing import Dict, Any

class GenWebSkill(BaseSkill):
    """
    Skill for generating full-stack web projects using Firecracker microVMs.
    Each user gets an isolated, high-performance VM environment.
    """
    
    async def create_fullstack_project(self, project_name: str, tech_stack: str, user_id: str) -> str:
        """
        Generates a full-stack project inside a Firecracker MicroVM.
        
        Args:
            project_name (str): Name of the project.
            tech_stack (str): Desired tech stack (e.g., 'Next.js + FastAPI').
            user_id (str): The ID of the user (injected by system).
            
        Returns:
            str: Summary of the generated project and VNC connection info.
        """
        # 1. Start/Get the Firecracker VM for the user
        try:
            vm = firecracker_manager.start_vm(user_id)
        except Exception as e:
            return f"Failed to initialize Firecracker Sandbox: {str(e)}"
            
        # 2. Execute generation commands inside the VM
        # In a real setup, we'd use a guest agent via VSOCK.
        commands = [
            f"mkdir -p /home/user/{project_name}",
            f"cd /home/user/{project_name} && npm init -y",
            f"echo 'Project: {project_name}' > /home/user/{project_name}/README.md"
        ]
        
        for cmd in commands:
            firecracker_manager.execute_in_vm(user_id, cmd)
            
        return (
            f"Successfully generated project '{project_name}' in a Firecracker MicroVM.\n"
            f"VNC Visual Stream: available at port {vm.vnc_proxy_port}\n"
            f"VM Internal IP: {vm.ip_address}"
        )

    async def run_shell_command(self, command: str, user_id: str) -> str:
        """
        Runs a shell command inside the user's Firecracker VM.
        
        Args:
            command (str): The shell command to execute.
            user_id (str): The ID of the user.
            
        Returns:
            str: Command output.
        """
        result = firecracker_manager.execute_in_vm(user_id, command)
        return result["stdout"] if result["exit_code"] == 0 else f"Error: {result['stderr']}"
