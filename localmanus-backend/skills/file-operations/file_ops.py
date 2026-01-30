import os
from core.skill_manager import BaseSkill


class FileOperationSkill(BaseSkill):
    """
    Standardized skill for basic file operations.
    """

    def __init__(self):
        super().__init__()
        self.name = "file_operation"
        self.description = "Skill for basic file operations including read, write, and list."

    def file_read(self, file_path: str) -> str:
        """
        Reads the content of a file.

        Args:
            file_path (str): Path to the file to read

        Returns:
            str: Content of the file or error message
        """
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist."
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def file_write(self, file_path: str, content: str) -> str:
        """
        Writes content to a file.

        Args:
            file_path (str): Path to the file to write
            content (str): Content to write to the file

        Returns:
            str: Success message or error message
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def directory_list(self, directory: str = ".") -> str:
        """
        Lists contents of a directory.

        Args:
            directory (str): Path to the directory to list (default: current directory)

        Returns:
            str: List of directory contents or error message
        """
        try:
            items = os.listdir(directory)
            return "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {str(e)}"


class FileOps(BaseSkill):
    """
    Legacy class maintained for backward compatibility.
    Use FileOperationSkill instead.
    """
    
    def __init__(self):
        super().__init__()
        self.file_operation_skill = FileOperationSkill()

    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a file.
        
        Args:
            file_path (str): Path to the file to read
        
        Returns:
            str: Content of the file or error message
        """
        return self.file_operation_skill.file_read(file_path)

    def write_file(self, file_path: str, content: str) -> str:
        """
        Writes content to a file.
        
        Args:
            file_path (str): Path to the file to write
            content (str): Content to write to the file
        
        Returns:
            str: Success message or error message
        """
        return self.file_operation_skill.file_write(file_path, content)

    def list_dir(self, directory: str = ".") -> str:
        """
        Lists contents of a directory.
        
        Args:
            directory (str): Path to the directory to list (default: current directory)
        
        Returns:
            str: List of directory contents or error message
        """
        return self.file_operation_skill.directory_list(directory)
