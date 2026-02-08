import os
from pathlib import Path
from typing import Optional
from core.skill_manager import BaseSkill
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock


class FileOperationSkill(BaseSkill):
    """Standardized skill for basic file operations."""

    def __init__(self):
        super().__init__()
        self.name = "file_operation"
        self.description = "Skill for basic file operations including read, write, and list."
        self.upload_base_dir = Path("uploads")

    def _get_user_dir(self, user_id: Optional[int] = None) -> Path:
        """Get user-specific upload directory"""
        if user_id:
            return self.upload_base_dir / str(user_id)
        return Path(".")

    def list_user_files(self, user_id: int) -> ToolResponse:
        """Lists all files uploaded by a specific user.

        Args:
            user_id (int): ID of the user

        Returns:
            ToolResponse: List of files or error message
        """
        try:
            user_dir = self._get_user_dir(user_id)
            if not user_dir.exists():
                return ToolResponse(content=[TextBlock(type="text", text="No files uploaded yet.")])
            
            files = []
            for item in user_dir.iterdir():
                if item.is_file():
                    file_info = f"- {item.name} ({item.stat().st_size} bytes)"
                    files.append(file_info)
            
            if not files:
                content = "No files found in your upload directory."
            else:
                content = "Your uploaded files:\n" + "\n".join(files)
            
            return ToolResponse(content=[TextBlock(type="text", text=content)])
        except Exception as e:
            error_msg = f"Error listing user files: {str(e)}"
            return ToolResponse(content=[TextBlock(type="text", text=error_msg)])

    def read_user_file(self, user_id: int, filename: str) -> ToolResponse:
        """Reads a file from user's upload directory.

        Args:
            user_id (int): ID of the user
            filename (str): Name of the file to read

        Returns:
            ToolResponse: Content of the file or error message
        """
        try:
            user_dir = self._get_user_dir(user_id)
            file_path = user_dir / filename
            
            if not file_path.exists():
                return ToolResponse(content=[TextBlock(type="text", text=f"File '{filename}' not found in your uploads.")])
            
            if not file_path.is_relative_to(user_dir):
                return ToolResponse(content=[TextBlock(type="text", text="Access denied: Invalid file path.")])
            
            # Try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return ToolResponse(content=[TextBlock(type="text", text=f"Content of {filename}:\n\n{content}")])
            except UnicodeDecodeError:
                # Binary file
                file_size = file_path.stat().st_size
                return ToolResponse(content=[TextBlock(type="text", text=f"{filename} is a binary file ({file_size} bytes). Cannot display content.")])
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            return ToolResponse(content=[TextBlock(type="text", text=error_msg)])

    def file_read(self, file_path: str) -> ToolResponse:
        """Reads the content of a file.

        Args:
            file_path (str): Path to the file to read

        Returns:
            ToolResponse: Content of the file or error message
        """
        if not os.path.exists(file_path):
            return ToolResponse(content=[TextBlock(type="text", text=f"Error: File {file_path} does not exist.")])
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ToolResponse(content=[TextBlock(type="text", text=content)])
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"Error reading file: {str(e)}")])

    def file_write(self, file_path: str, content: str) -> ToolResponse:
        """Writes content to a file.

        Args:
            file_path (str): Path to the file to write
            content (str): Content to write to the file

        Returns:
            ToolResponse: Success message or error message
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResponse(content=[TextBlock(type="text", text=f"Successfully wrote to {file_path}")])
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"Error writing file: {str(e)}")])

    def directory_list(self, directory: str = ".") -> ToolResponse:
        """Lists contents of a directory.

        Args:
            directory (str): Path to the directory to list (default: current directory)

        Returns:
            ToolResponse: List of directory contents or error message
        """
        try:
            items = os.listdir(directory)
            content = "\n".join(items)
            return ToolResponse(content=[TextBlock(type="text", text=content)])
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"Error listing directory: {str(e)}")])


class FileOps(BaseSkill):
    """Legacy class maintained for backward compatibility."""
    
    def __init__(self):
        super().__init__()
        self.file_operation_skill = FileOperationSkill()

    def read_file(self, file_path: str) -> ToolResponse:
        """Reads the content of a file."""
        return self.file_operation_skill.file_read(file_path)

    def write_file(self, file_path: str, content: str) -> ToolResponse:
        """Writes content to a file."""
        return self.file_operation_skill.file_write(file_path, content)

    def list_dir(self, directory: str = ".") -> ToolResponse:
        """Lists contents of a directory."""
        return self.file_operation_skill.directory_list(directory)

    def list_user_files(self, user_id: int) -> ToolResponse:
        """Lists all files uploaded by a specific user."""
        return self.file_operation_skill.list_user_files(user_id)

    def read_user_file(self, user_id: int, filename: str) -> ToolResponse:
        """Reads a file from user's upload directory."""
        return self.file_operation_skill.read_user_file(user_id, filename)
