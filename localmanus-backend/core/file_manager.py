"""
Unified File Manager for LocalManus

Abstracts file operations across host and sandbox environments.
Skills don't care where files are - they just use FileManager.
"""

import os
import logging
from typing import Optional, Union, Dict, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger("LocalManus-FileManager")


class StorageLocation(Enum):
    """File storage location options"""
    HOST = "host"           # Store on host machine
    SANDBOX = "sandbox"     # Store in user sandbox
    AUTO = "auto"          # Decide based on path and config


class FileManager:
    """
    Unified file manager that handles both host and sandbox storage.
    
    Usage:
        fm = FileManager(sandbox_manager, user_id)
        
        # Write file (auto-routes to appropriate location)
        await fm.write("/home/gem/project/main.py", code_content)
        
        # Read file
        content = await fm.read("/home/gem/project/main.py")
        
        # Check exists
        if await fm.exists("/home/gem/data.json"):
            ...
    """
    
    def __init__(
        self, 
        sandbox_manager,
        user_id: str,
        default_location: StorageLocation = StorageLocation.SANDBOX
    ):
        self.sandbox_manager = sandbox_manager
        self.user_id = user_id
        self.default_location = default_location
        self._sandbox_client = None
        self._sandbox_info = None
    
    def _get_sandbox_client(self):
        """Lazy load sandbox client"""
        if self._sandbox_client is None:
            self._sandbox_client = self.sandbox_manager.get_client(self.user_id)
            self._sandbox_info = self.sandbox_manager.get_sandbox(self.user_id)
        return self._sandbox_client
    
    def _resolve_location(self, path: str, location: StorageLocation) -> StorageLocation:
        """Determine where to store the file"""
        if location != StorageLocation.AUTO:
            return location
        
        # Auto-detect: sandbox paths go to sandbox, others to host
        if path.startswith('/home/') or path.startswith('/tmp/'):
            return StorageLocation.SANDBOX
        
        # Default based on configuration
        return self.default_location
    
    async def write(
        self, 
        path: str, 
        content: Union[str, bytes],
        location: StorageLocation = StorageLocation.AUTO
    ) -> Dict[str, Any]:
        """
        Write file to storage.
        
        Args:
            path: File path (can be absolute or relative)
            content: File content (str or bytes)
            location: Where to store (HOST, SANDBOX, or AUTO)
            
        Returns:
            Dict with 'success', 'path', 'location' keys
        """
        target = self._resolve_location(path, location)
        
        try:
            if target == StorageLocation.SANDBOX:
                client = self._get_sandbox_client()
                
                # Ensure directory exists
                dir_path = '/'.join(path.split('/')[:-1])
                if dir_path:
                    client.exec_command(f"mkdir -p {dir_path}")
                
                # Write file
                if isinstance(content, bytes):
                    client.upload_file(path, content)
                else:
                    client.write_file(path, content)
                
                logger.debug(f"Written to sandbox: {path}")
                return {"success": True, "path": path, "location": "sandbox"}
            
            else:
                # Write to host
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                mode = 'wb' if isinstance(content, bytes) else 'w'
                with open(path, mode) as f:
                    f.write(content)
                
                logger.debug(f"Written to host: {path}")
                return {"success": True, "path": path, "location": "host"}
                
        except Exception as e:
            logger.error(f"Failed to write {path}: {e}")
            return {"success": False, "error": str(e), "path": path}
    
    async def read(
        self, 
        path: str,
        location: StorageLocation = StorageLocation.AUTO,
        binary: bool = False
    ) -> Union[str, bytes, None]:
        """
        Read file from storage.
        
        Args:
            path: File path
            location: Where to read from (AUTO tries sandbox first, then host)
            binary: If True, return bytes; otherwise return str
            
        Returns:
            File content or None if not found
        """
        target = self._resolve_location(path, location)
        
        try:
            if target == StorageLocation.SANDBOX:
                client = self._get_sandbox_client()
                content = client.read_file(path)
                return content.encode() if binary and content else content
            
            else:
                mode = 'rb' if binary else 'r'
                with open(path, mode) as f:
                    return f.read()
                    
        except Exception as e:
            logger.error(f"Failed to read {path}: {e}")
            return None
    
    async def exists(self, path: str, location: StorageLocation = StorageLocation.AUTO) -> bool:
        """Check if file exists"""
        target = self._resolve_location(path, location)
        
        try:
            if target == StorageLocation.SANDBOX:
                client = self._get_sandbox_client()
                result = client.exec_command(f"test -f {path} && echo 'exists'")
                return 'exists' in str(result)
            else:
                return Path(path).exists()
        except:
            return False
    
    async def list_dir(
        self, 
        path: str, 
        location: StorageLocation = StorageLocation.AUTO
    ) -> list:
        """List directory contents"""
        target = self._resolve_location(path, location)
        
        try:
            if target == StorageLocation.SANDBOX:
                client = self._get_sandbox_client()
                return client.list_files(path)
            else:
                return [
                    {"name": f.name, "type": "file" if f.is_file() else "dir"}
                    for f in Path(path).iterdir()
                ]
        except Exception as e:
            logger.error(f"Failed to list {path}: {e}")
            return []
    
    def get_sandbox_home(self) -> str:
        """Get user's sandbox home directory"""
        if self._sandbox_info is None:
            self._sandbox_info = self.sandbox_manager.get_sandbox(self.user_id)
        return self._sandbox_info.home_dir or '/home/gem'
    
    def resolve_path(self, path: str) -> str:
        """
        Resolve a path relative to sandbox home if not absolute.
        
        Examples:
            "project/main.py" -> "/home/gem/project/main.py"
            "/tmp/test.txt" -> "/tmp/test.txt" (unchanged)
        """
        if path.startswith('/'):
            return path
        return f"{self.get_sandbox_home()}/{path}"


# Global helper for skill usage
async def get_file_manager(user_id: str) -> FileManager:
    """Get FileManager instance for user"""
    from core.firecracker_sandbox import sandbox_manager
    return FileManager(sandbox_manager, user_id)
