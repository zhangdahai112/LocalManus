"""ReAct Agent with SSE Streaming Support using Native AgentScope API.

This module implements a ReAct (Reasoning and Acting) agent that uses AgentScope's
native ReActAgent with proper skill integration and streaming support.
"""

import json
import logging
import datetime
import asyncio
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
            toolkit=skill_manager.toolkit
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
        Streaming ReAct loop using AgentScope's native agent capabilities.
        
        This method uses the parent ReActAgent's built-in reply mechanism
        which handles streaming, tool execution, and the ReAct loop internally.
        """
        new_messages = []
        
        try:
            # Convert dict messages to Msg objects if needed
            msg_objects = []
            for m in messages:
                if isinstance(m, dict):
                    msg_objects.append(Msg(
                        name=m.get("name", "User"),
                        content=m["content"],
                        role=m["role"]
                    ))
                else:
                    msg_objects.append(m)
            
            # Get the last user message to respond to
            last_msg = msg_objects[-1] if msg_objects else None
            
            if not last_msg:
                yield {"content": "Error: No message to respond to."}
                return
            
            # Call the parent ReActAgent's reply method
            # This handles the full ReAct loop including tool calls
            response = await self.reply(last_msg)
            
            # Extract and yield the response content
            if response:
                content = self._extract_content(response)
                if content:
                    yield {"content": content}
                
                # Add to history sync
                if hasattr(response, 'role') and hasattr(response, 'content'):
                    new_messages.append({
                        "role": response.role,
                        "content": response.content
                    })
                
                # Check for tool calls in response
                tool_calls = self._extract_tool_calls(response)
                if tool_calls:
                    for tc in tool_calls:
                        name = tc.get('function', {}).get('name', tc.get('name', 'unknown'))
                        yield {"content": f"\n\n🔧 **[Tool Used]**: `{name}`\n"}
                    
        except Exception as e:
            logger.error(f"Error in ReAct loop: {str(e)}", exc_info=True)
            yield {"content": f"\n\n❌ **[Error]**: {str(e)}\n"}
        
        finally:
            if new_messages:
                yield {"_sync": new_messages}
    
    def _extract_tool_call_from_chunk(self, chunk) -> Optional[Dict]:
        """Extract tool call information from a streaming chunk.
        
        This allows us to detect tool calls during streaming without re-parsing.
        Supports OpenAI streaming format with tool_calls in delta.
        """
        # Dictionary format (OpenAI streaming)
        if isinstance(chunk, dict):
            # OpenAI format: choices[0].delta.tool_calls
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                tool_calls = delta.get('tool_calls', [])
                if tool_calls:
                    # Return the first tool call
                    tc = tool_calls[0]
                    return {
                        'function': {
                            'name': tc.get('function', {}).get('name', ''),
                            'arguments': tc.get('function', {}).get('arguments', '')
                        }
                    }
            # Direct tool_calls in dictionary (skip if already checked above)
            return None
        
        # Object with tool_calls attribute (non-dict objects only)
        try:
            if hasattr(chunk, 'tool_calls'):
                tool_calls = getattr(chunk, 'tool_calls', None)
                if tool_calls and len(tool_calls) > 0:
                    tc = tool_calls[0]
                    return {
                        'function': {
                            'name': getattr(tc, 'name', getattr(tc, 'function', {}).get('name', '')),
                            'arguments': getattr(tc, 'arguments', getattr(tc, 'function', {}).get('arguments', ''))
                        }
                    }
        except (AttributeError, IndexError, KeyError, TypeError) as e:
            # Silently ignore attribute errors during tool_calls extraction
            pass
        
        return None
    
    def _extract_token_from_chunk(self, chunk) -> str:
        """Extract token text from various streaming chunk formats."""
        # Direct string
        if isinstance(chunk, str):
            return chunk
        
        # Object with content attribute
        if hasattr(chunk, 'content'):
            content = chunk.content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from content blocks
                texts = []
                for block in content:
                    if hasattr(block, 'text'):
                        texts.append(block.text)
                    elif isinstance(block, dict) and 'text' in block:
                        texts.append(block['text'])
                return ''.join(texts)
        
        # Dictionary format
        if isinstance(chunk, dict):
            # OpenAI format: choices[0].delta.content
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                return delta.get('content', '')
            # Simple format
            return chunk.get('content', chunk.get('text', ''))
        
        # Msg object
        if hasattr(chunk, 'content'):
            return str(chunk.content)
        
        return ''
    
    def _extract_content(self, reply_msg) -> str:
        """Extract text content from AgentScope message object."""
        if hasattr(reply_msg, 'content'):
            if isinstance(reply_msg.content, list):
                # Handle list of content blocks
                content_blocks = []
                for block in reply_msg.content:
                    if hasattr(block, 'text'):
                        content_blocks.append(block.text)
                    elif isinstance(block, dict) and 'text' in block:
                        content_blocks.append(block['text'])
                    else:
                        content_blocks.append(str(block))
                return "".join(content_blocks)
            else:
                return str(reply_msg.content)
        return ""
    
    def _extract_tool_calls(self, reply_msg) -> list:
        """Extract tool calls from AgentScope message object."""
        tool_calls = []
        if hasattr(reply_msg, 'content') and isinstance(reply_msg.content, list):
            for block in reply_msg.content:
                if hasattr(block, 'type') and block.type == 'tool_use':
                    tool_calls.append({
                        'function': {
                            'name': getattr(block, 'name', 'unknown')
                        }
                    })
                elif isinstance(block, dict) and block.get('type') == 'tool_use':
                    tool_calls.append({
                        'function': {
                            'name': block.get('name', 'unknown')
                        }
                    })
        return tool_calls

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
        # Convert user input to messages format expected by run_stream
        messages = [{"role": "user", "content": user_input}]
        async for chunk in self.run_stream(messages):
            yield chunk
