import os
import subprocess
import json
import time
import logging
import socket
import requests
import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("LocalManus-Sandbox")

class SandboxMode(Enum):
    """Sandbox execution mode"""
    LOCAL = "local"  # Connect to existing local sandbox
    ONLINE = "online"  # Spin up new Docker containers

@dataclass
class SandboxInfo:
    """Sandbox instance information"""
    sandbox_id: str
    base_url: str
    mode: SandboxMode
    container_id: Optional[str] = None
    vnc_url: Optional[str] = None
    vscode_url: Optional[str] = None
    home_dir: Optional[str] = None

class SandboxClient:
    """
    Client for interacting with agent-infra/sandbox API.
    Supports both local connection and online Docker mode.
    """
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to sandbox API"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Sandbox API error: {e}")
            raise
    
    def get_context(self) -> Dict[str, Any]:
        """Get sandbox context information"""
        return self._request('GET', '/v1/sandbox')
    
    def exec_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute shell command in sandbox"""
        payload = {'command': command}
        if cwd:
            payload['cwd'] = cwd
        return self._request('POST', '/v1/shell/exec', json=payload)
    
    def read_file(self, file_path: str) -> str:
        """Read file from sandbox"""
        result = self._request('POST', '/v1/file/read', json={'file': file_path})
        return result.get('data', {}).get('content', '')
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Write file to sandbox"""
        return self._request('POST', '/v1/file/write', json={
            'file': file_path,
            'content': content
        })
    
    def list_files(self, path: str) -> List[Dict[str, Any]]:
        """List files in directory"""
        result = self._request('POST', '/v1/file/list', json={'path': path})
        return result.get('data', {}).get('files', [])
    
    def screenshot(self) -> bytes:
        """Take browser screenshot"""
        result = self._request('POST', '/v1/browser/screenshot')
        # Assuming the API returns base64 encoded image
        import base64
        img_data = result.get('data', {}).get('screenshot', '')
        return base64.b64decode(img_data) if img_data else b''
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get browser CDP URL and info"""
        return self._request('GET', '/v1/browser/info')
    
    def browser_execute_action(self, action_type: str, **params) -> Dict[str, Any]:
        """Execute a GUI action in the sandbox browser (click, type, scroll, etc.)"""
        payload = {"action": {"type": action_type, **params}}
        return self._request('POST', '/v1/browser/action', json=payload)
    
    def execute_jupyter_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code in Jupyter kernel"""
        return self._request('POST', '/v1/jupyter/execute', json={'code': code})

class SandboxManager:
    """
    Unified Sandbox Manager supporting both Local and Online modes.
    - Local Mode: Connect to pre-existing sandbox at http://192.168.126.131:8080
    - Online Mode: Spin up new Docker containers on demand
    """
    DOCKER_IMAGE = "ghcr.io/agent-infra/sandbox:latest"
    DOCKER_IMAGE_CN = "enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest"
    
    def __init__(self, 
                 mode: SandboxMode = SandboxMode.LOCAL,
                 local_url: str = "http://192.168.126.131:8080",
                 use_china_mirror: bool = False):
        self.mode = mode
        self.local_url = local_url
        self.use_china_mirror = use_china_mirror
        self.sandboxes: Dict[str, SandboxInfo] = {}
        
        logger.info(f"Initialized SandboxManager in {mode.value} mode")
        
        # Test local connection if in local mode
        if mode == SandboxMode.LOCAL:
            self._test_local_connection()
    
    def _test_local_connection(self):
        """Test connection to local sandbox"""
        try:
            client = SandboxClient(self.local_url)
            context = client.get_context()
            logger.info(f"Successfully connected to local sandbox: {context}")
        except Exception as e:
            logger.warning(f"Cannot connect to local sandbox at {self.local_url}: {e}")
            logger.warning("You may need to start the local sandbox first")
    
    def _start_docker_container(self, user_id: str, port: int = None) -> SandboxInfo:
        """Start a new Docker container for online mode"""
        if port is None: 
            # Auto-assign port based on user_id
            port = 8080 + (hash(user_id) % 1000)
        
        image = self.DOCKER_IMAGE_CN if self.use_china_mirror else self.DOCKER_IMAGE
        container_name = f"localmanus-sandbox-{user_id}"
        
        # Check if container already exists
        check_cmd = ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.ID}}"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if result.stdout.strip():
            container_id = result.stdout.strip()
            logger.info(f"Container {container_name} already exists: {container_id}")
            
            # Check if running
            status_cmd = ["docker", "inspect", "-f", "{{.State.Running}}", container_id]
            status = subprocess.run(status_cmd, capture_output=True, text=True)
            
            if status.stdout.strip() == "true":
                logger.info(f"Container {container_name} is already running")
            else:
                # Start existing container
                logger.info(f"Starting existing container {container_name}")
                subprocess.run(["docker", "start", container_id], check=True)
        else:
            # Create and start new container
            logger.info(f"Creating new container {container_name} on port {port}")
            cmd = [
                "docker", "run",
                "--security-opt", "seccomp=unconfined",
                "--name", container_name,
                "-d",  # Detached mode
                "-p", f"{port}:8080",
                "--shm-size", "2gb",
                image
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            container_id = result.stdout.strip()
            logger.info(f"Started container {container_id} for user {user_id}")
            
            # Wait for container to be ready
            time.sleep(3)
        
        base_url = f"http://localhost:{port}"
        sandbox_info = SandboxInfo(
            sandbox_id=user_id,
            base_url=base_url,
            mode=SandboxMode.ONLINE,
            container_id=container_id,
            vnc_url=f"{base_url}/vnc/index.html?autoconnect=true",
            vscode_url=f"{base_url}/code-server/"
        )
        
        # Get home directory
        try:
            client = SandboxClient(base_url)
            context = client.get_context()
            sandbox_info.home_dir = context.get('data', {}).get('home_dir', '/home/gem')
        except Exception as e:
            logger.warning(f"Could not get sandbox context: {e}")
            sandbox_info.home_dir = '/home/gem'
        
        return sandbox_info
    
    def get_sandbox(self, user_id: str) -> SandboxInfo:
        """Get or create sandbox for user"""
        if user_id in self.sandboxes:
            return self.sandboxes[user_id]
        
        if self.mode == SandboxMode.LOCAL:
            # Use shared local sandbox
            sandbox_info = SandboxInfo(
                sandbox_id="local-shared",
                base_url=self.local_url,
                mode=SandboxMode.LOCAL,
                vnc_url=f"{self.local_url}/vnc/index.html?autoconnect=true",
                vscode_url=f"{self.local_url}/code-server/"
            )
            
            # Get home directory
            try:
                client = SandboxClient(self.local_url)
                context = client.get_context()
                sandbox_info.home_dir = context.get('data', {}).get('home_dir', '/home/gem')
            except Exception as e:
                logger.warning(f"Could not get sandbox context: {e}")
                sandbox_info.home_dir = '/home/gem'
        else:
            # Create new Docker container
            sandbox_info = self._start_docker_container(user_id)
        
        self.sandboxes[user_id] = sandbox_info
        return sandbox_info
    
    def get_client(self, user_id: str) -> SandboxClient:
        """Get API client for user's sandbox"""
        sandbox_info = self.get_sandbox(user_id)
        return SandboxClient(sandbox_info.base_url)
    
    def execute_command(self, user_id: str, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute command in user's sandbox"""
        client = self.get_client(user_id)
        return client.exec_command(command, cwd)
    
    def cleanup_sandbox(self, user_id: str):
        """Cleanup sandbox resources"""
        if user_id not in self.sandboxes:
            logger.warning(f"No sandbox found for user {user_id}")
            return
        
        sandbox_info = self.sandboxes[user_id]
        
        if sandbox_info.mode == SandboxMode.ONLINE and sandbox_info.container_id:
            # Stop and remove Docker container
            try:
                logger.info(f"Stopping container {sandbox_info.container_id}")
                subprocess.run(["docker", "stop", sandbox_info.container_id], 
                             timeout=30, check=True)
                subprocess.run(["docker", "rm", sandbox_info.container_id], check=True)
                logger.info(f"Removed container for user {user_id}")
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout stopping container {sandbox_info.container_id}")
                subprocess.run(["docker", "kill", sandbox_info.container_id])
                subprocess.run(["docker", "rm", sandbox_info.container_id])
            except Exception as e:
                logger.error(f"Error cleaning up container: {e}")
        
        del self.sandboxes[user_id]
        logger.info(f"Cleaned up sandbox for user {user_id}")
    
    def cleanup_all(self):
        """Cleanup all sandbox resources"""
        for user_id in list(self.sandboxes.keys()):
            self.cleanup_sandbox(user_id)

# Global Instance - Default to LOCAL mode for development
# Change to ONLINE mode in production or when you need isolated containers
try:
    from core.config import SANDBOX_MODE, SANDBOX_LOCAL_URL, USE_CHINA_MIRROR
    mode = SandboxMode.ONLINE if SANDBOX_MODE.lower() == 'online' else SandboxMode.LOCAL
except ImportError:
    mode = SandboxMode.LOCAL
    SANDBOX_LOCAL_URL = os.getenv('SANDBOX_LOCAL_URL', 'http://192.168.126.131:8080')
    USE_CHINA_MIRROR = os.getenv('USE_CHINA_MIRROR', 'false').lower() == 'true'

sandbox_manager = SandboxManager(
    mode=mode,
    local_url=SANDBOX_LOCAL_URL,
    use_china_mirror=USE_CHINA_MIRROR
)

# Legacy compatibility alias
firecracker_manager = sandbox_manager
