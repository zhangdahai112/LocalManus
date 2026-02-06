"""ReAct Agent with SSE Streaming Support using Native AgentScope API.

This module implements a ReAct (Reasoning and Acting) agent that uses AgentScope's
native ReActAgent with proper skill integration and streaming support.
"""

import json
import logging
import datetime
from typing import Dict, Any, Optional, AsyncGenerator
from agentscope.agent import ReActAgent as ASReActAgent
from agentscope.message import Msg
from core.skill_manager import SkillManager
from core.prompts import REACT_AGENT_SYSTEM_PROMPT

logger = logging.getLogger("LocalManus-ReActAgent")


class ReActAgent(ASReActAgent):
    """Standardized ReAct Agent following AgentScope patterns."""
    
    def __init__(self, model, formatter, skill_manager: SkillManager):
        """Initialize the ReAct agent with AgentScope native implementation."""
        # Initialize parent ReActAgent with toolkit
        super().__init__(
            name="LocalManus-ReAct",
            sys_prompt="",  # Will be set dynamically for each conversation
            model=model,
            formatter=formatter,
            toolkit=skill_manager.toolkit,
            max_iters=10  # Maximum ReAct iterations
        )
        self.skill_manager = skill_manager
        self.original_model = model  # Keep reference for streaming if needed

    def _build_system_prompt(self, user_context: Optional[Dict] = None) -> str:
        """Build system prompt with current context and tools."""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_info_str = json.dumps(user_context, ensure_ascii=False) if user_context else "Anonymous"
        skills_prompt = self.skill_manager.get_skills_prompt() or ""
        
        # Get tools metadata from toolkit
        tools_schemas = self.skill_manager.toolkit.get_json_schemas()
        tools_metadata = json.dumps(tools_schemas, indent=2, ensure_ascii=False)
        
        return REACT_AGENT_SYSTEM_PROMPT.format(
            current_time=current_time,
            user_info=user_info_str,
            skills_prompt=skills_prompt,
            tools_metadata=tools_metadata
        )

    async def run_stream(self, messages: list) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Performs the full ReAct loop (Think-Act-Observe) in a streaming fashion.
        
        Yields:
            - {'content': str}: Streaming content chunks for SSE
            - {'_sync': list}: Internal event with new messages to sync to history (at end)
            - {'_meta': dict}: Optional metadata about the run (iterations, etc.)
        
        Contract:
            - Orchestrator should filter out '_sync' and '_meta' events before sending to frontend
            - '_sync' contains all new messages added during this run
        """
        new_messages = []  # Track messages added during this run
        
        try:
            full_response = ""
            tool_calls = []
            
            # Obtain the stream object by awaiting the model call
            stream = await self(messages)
            async for chunk in stream:
                # 1. Handle content streaming
                if content := chunk.get("content"):
                    content_str = ""
                    if isinstance(content, list):
                        content_str = "".join([
                            b.get("text", b.text if hasattr(b, "text") else str(b)) 
                            if isinstance(b, (dict, object)) else str(b) 
                            for b in content
                        ])
                    else:
                        content_str = str(content)
                    
                    content_str = content_str[len(full_response):]
                    full_response += content_str
                    yield {"content": content_str}
                
                # 2. Accumulate tool calls
                if tc := chunk.get("tool_calls"):
                    tool_calls.extend(tc)
            
            # Record assistant response in context
            if full_response:
                assistant_msg = {"role": "assistant", "content": full_response}
                messages.append(assistant_msg)
                new_messages.append(assistant_msg)
            
            # If no tool calls, the agent has provided a final answer
            if not tool_calls:
                return
            
            # 3. Handle Tool Execution Turn
            for tc in tool_calls:
                name = tc.get('function', {}).get('name', tc.get('name', 'unknown'))
                
                # Notify UI about tool usage
                yield {"content": f"\n[Tool Use]: {name}\n"}
                
                # Execute tool via agent's toolkit
                observation = await self.execute_tool(tc)
                
                # Stream observation to UI
                yield {"content": f"\n[Observation]: {observation}\n"}
                
                # Persist observation to context
                system_msg = {"role": "system", "content": observation}
                messages.append(system_msg)
                new_messages.append(system_msg)
            
            # Yield metadata about the run (single turn mode)
            yield {"_meta": {"tool_calls_made": len(tool_calls) > 0, "needs_continuation": True}}
                    
        except Exception as e:
            logger.error(f"Error in ReAct loop: {str(e)}", exc_info=True)
            yield {"content": f"\n[Error]: {str(e)}"}
        
        finally:
            # Always yield sync event with new messages (even on error, sync partial progress)
            if new_messages:
                yield {"_sync": new_messages}

    async def execute_tool(self, tool_call: Dict) -> str:
        """Helper to execute a tool and return the observation string."""
        try:
            name = tool_call.get('function', {}).get('name', tool_call.get('name', 'unknown'))
            tool_res = await self.toolkit.call_tool_function(tool_call)
            
            # Normalize observation to string
            if isinstance(tool_res, list):
                return "".join([str(getattr(r, "content", r)) for r in tool_res])
            return str(tool_res)
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    async def run_with_context(self, user_input: str, user_context: Dict = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Alternative method name for compatibility with existing code.
        """
        async for chunk in self.run_stream(user_input, user_context=user_context):
            yield chunk
