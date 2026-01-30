import json
import uuid
from typing import List, Dict
from core.agent_manager import init_agents

class Orchestrator:
    def __init__(self):
        self.manager, self.planner = init_agents()

    async def run_workflow(self, user_input: str):
        """
        Executes the high-level orchestration flow.
        """
        # 1. Intent Analysis via Manager
        manager_resp = self.manager.process_input(user_input)
        intent_data = self._extract_json(manager_resp.content)
        
        # 2. DAG Generation via Planner
        planner_resp = self.planner.plan(json.dumps(intent_data))
        dag_plan = self._extract_json(planner_resp.content)
        
        # 3. Add system metadata
        dag_plan["trace_id"] = str(uuid.uuid4())
        
        return dag_plan

    def _extract_json(self, text: str) -> Dict:
        """
        Extracts JSON block from agent response.
        """
        try:
            # Simple extractor for markdown-wrapped JSON
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            return json.loads(json_str.strip())
        except Exception as e:
            return {"error": "Failed to parse JSON", "raw": text}

class SkillRegistry:
    """
    Registry of available skills that the Planner can choose from.
    """
    AVAILABLE_SKILLS = {
        "ppt_reader": {
            "path": "skills.ppt_tools.read_ppt",
            "description": "Extracts content from PPTX",
            "required_deps": ["python-pptx"]
        },
        "word_creator": {
            "path": "skills.word_tools.create_document",
            "description": "Generates Word DOCX",
            "required_deps": ["python-docx"]
        }
    }

    @classmethod
    def get_skill_metadata(cls, skill_name: str):
        return cls.AVAILABLE_SKILLS.get(skill_name)
