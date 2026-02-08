"""
Skill Registry for managing skill metadata and configurations
"""
import os
import json
import inspect
from typing import Dict, List, Any, Optional
from pathlib import Path
from core.skill_manager import SkillManager


class SkillRegistry:
    """Registry for skill metadata and configurations"""
    
    def __init__(self, skill_manager: SkillManager):
        self.skill_manager = skill_manager
        self.skills_dir = Path(skill_manager.skills_dir)
        
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all registered skills with metadata"""
        skills = []
        
        # Get all tools from toolkit
        tool_schemas = self.skill_manager.toolkit.get_json_schemas()
        
        # Group tools by skill/module
        skills_map = {}
        
        for tool in tool_schemas:
            # AgentScope wraps tool info in a 'function' key
            tool_info = tool.get("function", tool) if "function" in tool else tool
            
            # Extract skill name from function (e.g., "search_web" -> "web_search")
            func_name = tool_info.get("name", "")
            
            # Try to determine skill category
            skill_category = self._infer_skill_category(func_name, tool_info)
            
            if skill_category not in skills_map:
                skills_map[skill_category] = {
                    "id": skill_category,
                    "name": self._format_skill_name(skill_category),
                    "category": self._get_skill_category(skill_category),
                    "description": self._get_skill_description(skill_category),
                    "icon": self._get_skill_icon(skill_category),
                    "enabled": True,
                    "tools": [],
                    "config": self._load_skill_config(skill_category)
                }
            
            # Add tool to skill
            skills_map[skill_category]["tools"].append({
                "name": tool_info.get("name"),
                "description": tool_info.get("description", ""),
                "parameters": tool_info.get("parameters", {}),
                "required": tool_info.get("parameters", {}).get("required", [])
            })
        
        return list(skills_map.values())
    
    def _infer_skill_category(self, func_name: str, tool: Dict) -> str:
        """Infer skill category from function name"""
        if any(kw in func_name for kw in ["search", "scrape", "web"]):
            return "web_search"
        elif any(kw in func_name for kw in ["file", "read", "write", "directory", "list_user"]):
            return "file_operations"
        elif any(kw in func_name for kw in ["gen", "generate", "create"]):
            return "generation"
        elif any(kw in func_name for kw in ["execute", "run", "command"]):
            return "system_execution"
        else:
            return "general"
    
    def _format_skill_name(self, skill_id: str) -> str:
        """Format skill ID to display name"""
        name_map = {
            "web_search": "Web Search",
            "file_operations": "File Operations",
            "generation": "Content Generation",
            "system_execution": "System Execution",
            "general": "General Tools"
        }
        return name_map.get(skill_id, skill_id.replace("_", " ").title())
    
    def _get_skill_category(self, skill_id: str) -> str:
        """Get skill category"""
        category_map = {
            "web_search": "search",
            "file_operations": "file",
            "generation": "creative",
            "system_execution": "system",
            "general": "general"
        }
        return category_map.get(skill_id, "general")
    
    def _get_skill_description(self, skill_id: str) -> str:
        """Get skill description"""
        desc_map = {
            "web_search": "Search the web and scrape webpage content",
            "file_operations": "Read, write, and manage files",
            "generation": "Generate content, web pages, and documents",
            "system_execution": "Execute system commands and scripts",
            "general": "General utility tools"
        }
        return desc_map.get(skill_id, "")
    
    def _get_skill_icon(self, skill_id: str) -> str:
        """Get skill icon name (Lucide icon names)"""
        icon_map = {
            "web_search": "Search",
            "file_operations": "FileText",
            "generation": "Sparkles",
            "system_execution": "Terminal",
            "general": "Wrench"
        }
        return icon_map.get(skill_id, "Wrench")
    
    def _load_skill_config(self, skill_id: str) -> Dict[str, Any]:
        """Load skill configuration"""
        config_file = self.skills_dir / skill_id / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_skill_config(self, skill_id: str, config: Dict[str, Any]) -> bool:
        """Save skill configuration"""
        try:
            skill_dir = self.skills_dir / skill_id
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            config_file = skill_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving skill config: {e}")
            return False
    
    def get_skill_detail(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific skill"""
        all_skills = self.get_all_skills()
        for skill in all_skills:
            if skill["id"] == skill_id:
                return skill
        return None
    
    def update_skill_status(self, skill_id: str, enabled: bool) -> bool:
        """Update skill enabled status"""
        config = self._load_skill_config(skill_id)
        config["enabled"] = enabled
        return self.save_skill_config(skill_id, config)
