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

# Global callback for streaming thinking content
_thinking_callback = None

def set_thinking_callback(callback):
    """Set a callback function to receive thinking content stream.
    
    Args:
        callback: A function that receives thinking content chunks
    """
    global _thinking_callback
    _thinking_callback = callback


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
        
        Note: True token-by-token streaming through the ReAct loop is complex because
        the agent needs complete responses to decide on tool calls. We yield:
        1. Tool call notifications as they happen
        2. Final response content streamed progressively
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
            
            # Create a queue to receive content chunks
            content_queue = asyncio.Queue()
            response_holder = {"response": None, "done": False}
            
            async def generate_response():
                """Run the reply in background and stream chunks."""
                try:
                    # Call the parent ReActAgent's reply method
                    response = await self(last_msg)
                    response_holder["response"] = response
                    
                    if response:
                        content = self._extract_content(response)
                        
                        # Stream content in chunks
                        if content:
                            chunk_size = 10  # Characters per chunk
                            for i in range(0, len(content), chunk_size):
                                chunk = content[i:i + chunk_size]
                                await content_queue.put({"content": chunk})
                                # Small delay to allow consumer to process
                                await asyncio.sleep(0.01)
                        
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
                                await content_queue.put({"content": f"\n\n🔧 **[Tool Used]**: `{name}`\n"})
                
                except Exception as e:
                    logger.error(f"Error in generate_response: {e}")
                    await content_queue.put({"content": f"\n\n❌ **[Error]**: {str(e)}\n"})
                finally:
                    response_holder["done"] = True
                    await content_queue.put(None)  # Signal completion
            
            # Start the response generation task
            generation_task = asyncio.create_task(generate_response())
            
            # Yield an initial empty chunk to establish the connection
            yield {"content": ""}
            
            # Yield chunks as they become available
            try:
                while True:
                    chunk = await content_queue.get()
                    if chunk is None:
                        break
                    yield chunk
            finally:
                # Ensure the generation task is cleaned up
                if not generation_task.done():
                    generation_task.cancel()
                    try:
                        await generation_task
                    except asyncio.CancelledError:
                        pass
                    
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

    def _extract_text_from_chunk(self, chunk) -> str:
        """Extract text content from a streaming chunk."""
        # Direct string
        if isinstance(chunk, str):
            return chunk
        
        # Object with content attribute (AgentScope format)
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
        
        # Dictionary format (OpenAI streaming)
        if isinstance(chunk, dict):
            if 'choices' in chunk and len(chunk['choices']) > 0:
                delta = chunk['choices'][0].get('delta', {})
                return delta.get('content', '')
            return chunk.get('content', chunk.get('text', ''))
        
        return ''

    def _extract_tool_calls_from_text(self, text: str) -> list:
        """Extract tool calls from text content (for streaming responses)."""
        tool_calls = []
        # Look for tool_use patterns in the text
        # This is a simple heuristic - in practice, tool calls come through
        # the streaming API in a structured format
        import re
        # Pattern to match tool calls like <tool_use> or function_call patterns
        # This is model-dependent and may need adjustment
        return tool_calls

    async def _execute_tool_calls(self, tool_calls: list) -> list:
        """Execute tool calls and return results."""
        results = []
        for tc in tool_calls:
            try:
                result = await self.execute_tool(tc)
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing tool {tc}: {e}")
                results.append(f"Error: {str(e)}")
        return results

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

    async def run_with_context(self, user_input: str, user_context: Optional[Dict] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Alternative method name for compatibility with existing code.
        """
        # Convert user input to messages format expected by run_stream
        messages = [{"role": "user", "content": user_input}]
        async for chunk in self.run_stream(messages):
            yield chunk

    async def _reasoning(self, tool_choice: str | None = None) -> Msg:
        """Override _reasoning to stream thinking content to frontend.
        
        This method wraps the parent _reasoning and intercepts the streaming
        response to extract and forward thinking content.
        """
        global _thinking_callback
        
        # Import necessary modules from AgentScope
        from agentscope.agent._react_agent import _MemoryMark
        from agentscope.message import ToolResultBlock
        
        # Handle plan notebook hints (from parent implementation)
        if self.plan_notebook:
            # Insert the reasoning hint from the plan notebook
            hint_msg = await self.plan_notebook.get_current_hint()
            if self.print_hint_msg and hint_msg:
                await self.print(hint_msg)
            await self.memory.add(hint_msg, marks=_MemoryMark.HINT)

        # Convert Msg objects into the required format of the model API
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                *await self.memory.get_memory(),
            ],
        )
        # Clear the hint messages after use
        await self.memory.delete_by_mark(mark=_MemoryMark.HINT)

        res = await self.model(
            prompt,
            tools=self.toolkit.get_json_schemas(),
            tool_choice=tool_choice,
        )

        # handle output from the model
        interrupted_by_user = False
        msg = None

        # TTS model context manager
        from agentscope.agent._utils import _AsyncNullContext
        tts_context = self.tts_model or _AsyncNullContext()
        speech = None

        try:
            async with tts_context:
                msg = Msg(name=self.name, content=[], role="assistant")
                if self.model.stream:
                    async for content_chunk in res:
                        msg.content = content_chunk.content
                        
                        # Stream thinking content to frontend if callback is set
                        if _thinking_callback and hasattr(content_chunk, 'content'):
                            for block in content_chunk.content:
                                if hasattr(block, 'type') and block.type == 'thinking':
                                    thinking_text = getattr(block, 'text', '')
                                    if thinking_text:
                                        await _thinking_callback(thinking_text)
                                elif isinstance(block, dict) and block.get('type') == 'thinking':
                                    thinking_text = block.get('text', '')
                                    if thinking_text:
                                        await _thinking_callback(thinking_text)

                        # The speech generated from multimodal (audio) models
                        speech = msg.get_content_blocks("audio") or None

                        # Push to TTS model if available
                        if (
                            self.tts_model
                            and self.tts_model.supports_streaming_input
                        ):
                            tts_res = await self.tts_model.push(msg)
                            speech = tts_res.content

                        await self.print(msg, False, speech=speech)

                else:
                    msg.content = list(res.content)

                if self.tts_model:
                    # Push to TTS model and block to receive the full speech
                    # synthesis result
                    tts_res = await self.tts_model.synthesize(msg)
                    if self.tts_model.stream:
                        async for tts_chunk in tts_res:
                            speech = tts_chunk.content
                            await self.print(msg, False, speech=speech)
                    else:
                        speech = tts_res.content

                await self.print(msg, True, speech=speech)

                # Add a tiny sleep to yield the last message object in the
                # message queue
                await asyncio.sleep(0.001)

        except asyncio.CancelledError as e:
            interrupted_by_user = True
            raise e from None

        finally:
            # None will be ignored by the memory
            await self.memory.add(msg)

            # Post-process for user interruption
            if interrupted_by_user and msg:
                # Fake tool results
                tool_use_blocks = msg.get_content_blocks("tool_use")
                for tool_call in tool_use_blocks:
                    msg_res = Msg(
                        "system",
                        [
                            ToolResultBlock(
                                type="tool_result",
                                id=tool_call["id"],
                                name=tool_call["name"],
                                output="The tool call has been interrupted "
                                "by the user.",
                            ),
                        ],
                        "system",
                    )
                    await self.memory.add(msg_res)
                    await self.print(msg_res, True)
            
            return msg
