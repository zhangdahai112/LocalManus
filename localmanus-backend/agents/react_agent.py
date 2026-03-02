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
        Pure streaming ReAct loop - uses streaming interface for all LLM responses.
        
        This method streams tokens directly from the model as they are generated,
        providing real-time feedback to the user.
        """
        new_messages = []
        full_response = ""
        tool_calls_from_stream = []
        
        try:
            # Format messages for the model
            formatted_messages = messages
            if hasattr(self, 'formatter') and hasattr(self.formatter, 'format'):
                try:
                    format_res = self.formatter.format(messages)
                    formatted_messages = await format_res if hasattr(format_res, '__await__') else format_res
                except Exception as e:
                    logger.warning(f"Formatting failed: {e}")
            
            if not isinstance(formatted_messages, list):
                formatted_messages = [formatted_messages] if formatted_messages else []
            
            # Pure streaming - call model with stream=True
            model_result = self.original_model(formatted_messages, stream=True)
            response_stream = await model_result if hasattr(model_result, '__await__') else model_result
            
            # Process streaming response
            if hasattr(response_stream, '__anext__'):
                # Async generator
                async for chunk in response_stream:
                    token = self._extract_token_from_chunk(chunk)
                    if token:
                        delta = token[len(full_response):]
                        full_response += delta
                        yield {"content": delta}
                        await asyncio.sleep(0)
                    
                    tool_call = self._extract_tool_call_from_chunk(chunk)
                    if tool_call:
                        tool_calls_from_stream.append(tool_call)
            else:
                # Regular generator
                for chunk in response_stream:
                    token = self._extract_token_from_chunk(chunk)
                    if token:
                        delta = token[len(full_response):]
                        full_response += delta
                        yield {"content": delta}
                        await asyncio.sleep(0)
                    
                    tool_call = self._extract_tool_call_from_chunk(chunk)
                    if tool_call:
                        tool_calls_from_stream.append(tool_call)
            
            # Record assistant response
            if full_response:
                assistant_msg = {"role": "assistant", "content": full_response}
                messages.append(assistant_msg)
                new_messages.append(assistant_msg)
            
            # Execute tools if present
            if tool_calls_from_stream:
                logger.info(f"Using {len(tool_calls_from_stream)} tool calls from streaming chunks")
                
                for tc in tool_calls_from_stream:
                    name = tc.get('function', {}).get('name', tc.get('name', 'unknown'))
                    yield {"content": f"\n\n🔧 **[Using Tool]**: `{name}`\n"}
                    
                    observation = await self.execute_tool(tc)
                    yield {"content": f"📊 **[Result]**:\n{observation}\n\n"}
                    
                    system_msg = {"role": "system", "content": observation}
                    messages.append(system_msg)
                    new_messages.append(system_msg)
                
                yield {"_meta": {"tool_calls_made": True, "needs_continuation": True}}
                    
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
