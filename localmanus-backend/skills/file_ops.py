import os
from core.skill_manager import BaseSkill

class FileOps(BaseSkill):
    """
    Skill for basic file operations.
    """
    
    def read_file(self, file_path: str) -> str:
        """
        Reads the content of a file.
        """
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist."
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        """
        Writes content to a file.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def list_dir(self, directory: str = ".") -> str:
        """
        Lists contents of a directory.
        """
        try:
            items = os.listdir(directory)
            return "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {str(e)}"
