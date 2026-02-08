import json
import uuid
import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator
from core.agent_manager import init_agents
from agentscope.message import Msg

logger = logging.getLogger("LocalManus-Orchestrator")

class Orchestrator:
    def __init__(self):
        self.manager, self.planner, self.react_agent = init_agents()
        self.sessions: Dict[str, List[Msg]] = {}

    async def chat_stream(self, session_id: str, user_input: str, user_context: Dict = None, file_paths: List[str] = None) -> AsyncGenerator[str, None]:
        """
        Streaming chat with orchestrated ReAct loop and multi-round history.
        
        Architecture:
            - Orchestrator: Session management, SSE formatting, history sync
            - ReActAgent.run_stream: Full ReAct loop, yields content + internal sync events
        
        Internal Protocol:
            - {'content': str} -> Forward to frontend as SSE
            - {'_sync': list} -> Sync messages to session history (internal, not sent to frontend)
            - {'_meta': dict} -> Run metadata for logging (internal, not sent to frontend)
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        history = self.sessions[session_id]
        
        # 1. Check round limit
        if len(history) >= 40: 
             yield f"data: {json.dumps({'content': '[Error]: Reached maximum conversation limit.'}, ensure_ascii=False)}\n\n"
             return

        # 2. Append current user message to global history
        user_msg = Msg(name="User", content=user_input, role="user")
        history.append(user_msg)
        
        try:
            # 3. Prepare message list for the LLM
            # Convert history to Msg objects if needed
            msg_history = []
            for m in history:
                if isinstance(m, dict):
                    # Convert dict to Msg object
                    msg_history.append(Msg(name=m.get("name", "Unknown"), content=m["content"], role=m["role"]))
                else:
                    # Already a Msg object
                    msg_history.append(m)
            
            # Build system prompt with file paths context
            sys_prompt = self.react_agent._build_system_prompt(user_context)
            
            # Add file paths information if provided
            if file_paths:
                file_context = "\n\n**User's Uploaded Files:**\n"
                for file_path in file_paths:
                    file_context += f"- {file_path}\n"
                file_context += "\nYou can use 'read_user_file' tool to read these files. Extract the filename from the path."
                sys_prompt += file_context
            
            system_msg = Msg(name="System", content=sys_prompt, role="system")
            
            # Combine system message with history
            messages = [system_msg] + msg_history 

            # 4. Stream ReAct loop - handle internal protocol events
            async for chunk in self.react_agent.run_stream(messages):
                # Handle sync event (internal protocol)
                if "_sync" in chunk:
                    for m in chunk["_sync"]:
                        role = m.get("role")
                        content = m.get("content")
                        name = "ReActAgent" if role == "assistant" else "System"
                        history.append(Msg(name=name, content=content, role=role))
                    continue  # Don't forward to frontend
                
                # Handle metadata event (internal protocol)
                if "_meta" in chunk:
                    logger.debug(f"ReAct run metadata: {chunk['_meta']}")
                    continue  # Don't forward to frontend
                
                # Forward content chunks to frontend as SSE
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in orchestrated chat_stream: {str(e)}", exc_info=True)
            error_msg = f"\n[Error]: {str(e)}"
            yield f"data: {json.dumps({'content': error_msg}, ensure_ascii=False)}\n\n"

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
