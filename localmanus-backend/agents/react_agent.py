"""ReAct Agent with SSE Streaming Support using Native AgentScope API.

This module implements a ReAct (Reasoning and Acting) agent that uses AgentScope's
native ReActAgent with proper skill integration, streaming support, and memory compression.
"""

import json
import logging
import datetime
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, Type
from pydantic import BaseModel, Field
from agentscope.agent import ReActAgent as ASReActAgent
from agentscope.message import Msg
from agentscope.token import TokenCounterBase
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


# ============================================================================
# Memory Compression Schema
# ============================================================================

class CompressionSummarySchema(BaseModel):
    """Structured model for compressed memory summary."""

    task_overview: str = Field(
        max_length=300,
        description=(
            "The user's core request and success criteria. "
            "Any clarifications or constraints they specified"
        ),
    )
    current_state: str = Field(
        max_length=300,
        description=(
            "What has been completed so far. "
            "File created, modified, or analyzed (with paths if relevant). "
            "Key outputs or artifacts produced."
        ),
    )
    important_discoveries: str = Field(
        max_length=300,
        description=(
            "Technical constraints or requirements uncovered. "
            "Decisions made and their rationale. "
            "Errors encountered and how they were resolved. "
            "What approaches were tried that didn't work (and why)"
        ),
    )
    next_steps: str = Field(
        max_length=200,
        description=(
            "Specific actions needed to complete the task. "
            "Any blockers or open questions to resolve. "
            "Priority order if multiple steps remain"
        ),
    )
    context_to_preserve: str = Field(
        max_length=300,
        description=(
            "User preferences or style requirements. "
            "Domain-specific details that aren't obvious. "
            "Any promises made to the user"
        ),
    )


# ============================================================================
# Simple Token Counter
# ============================================================================

class SimpleTokenCounter(TokenCounterBase):
    """Simple token counter using character-based estimation.

    Uses a rough estimate of ~4 characters per token for most languages.
    For more accurate counting, consider using tiktoken for OpenAI models.
    """

    def __init__(self, chars_per_token: int = 4):
        self.chars_per_token = chars_per_token

    async def count(self, messages) -> int:
        """Count tokens in messages.

        Args:
            messages: Either a string or list of Msg objects

        Returns:
            Estimated token count
        """
        if isinstance(messages, str):
            return len(messages) // self.chars_per_token

        total_chars = 0
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, Msg):
                    content = msg.get_text_content() if hasattr(
                        msg, 'get_text_content') else str(msg.content)
                    total_chars += len(content)
                elif isinstance(msg, dict):
                    content = msg.get('content', '')
                    if isinstance(content, str):
                        total_chars += len(content)
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict):
                                total_chars += len(block.get('text', ''))
                            elif hasattr(block, 'text'):
                                total_chars += len(block.text)
                else:
                    total_chars += len(str(msg))
        else:
            total_chars = len(str(messages))

        return total_chars // self.chars_per_token


class ReActAgent(ASReActAgent):
    """Standardized ReAct Agent following AgentScope patterns.

    Features:
    - Memory compression when token count exceeds threshold
    - SSE streaming support
    - Tool execution via skill manager
    """

    # Compression configuration constants
    DEFAULT_COMPRESSION_THRESHOLD = 10000  # tokens
    DEFAULT_KEEP_RECENT = 3  # messages to keep uncompressed

    # Compression prompt template
    COMPRESSION_PROMPT = (
        "<system-hint>You have been working on the task described above "
        "but have not yet completed it. "
        "Now write a continuation summary that will allow you to resume "
        "work efficiently in a future context window where the "
        "conversation history will be replaced with this summary. "
        "Your summary should be structured, concise, and actionable."
        "</system-hint>"
    )

    # Summary template for compressed memory
    SUMMARY_TEMPLATE = (
        "<system-info>Here is a summary of your previous work\n"
        "# Task Overview\n"
        "{task_overview}\n\n"
        "# Current State\n"
        "{current_state}\n\n"
        "# Important Discoveries\n"
        "{important_discoveries}\n\n"
        "# Next Steps\n"
        "{next_steps}\n\n"
        "# Context to Preserve\n"
        "{context_to_preserve}"
        "</system-info>"
    )

    def __init__(
        self,
        model,
        formatter,
        skill_manager: SkillManager,
        enable_compression: bool = True,
        compression_threshold: int = None,
        keep_recent: int = None,
        compression_model=None,
        compression_formatter=None
    ):
        """Initialize the ReAct agent with AgentScope native implementation.

        Args:
            model: The LLM model to use
            formatter: Message formatter for the model
            skill_manager: SkillManager instance for tool execution
            enable_compression: Whether to enable memory compression (default: True)
            compression_threshold: Token threshold to trigger compression (default: 10000)
            keep_recent: Number of recent messages to keep uncompressed (default: 3)
            compression_model: Optional separate model for compression (default: use main model)
            compression_formatter: Optional formatter for compression model
        """
        # Build compression config if enabled
        compression_config = None
        if enable_compression:
            from agentscope.agent._react_agent import ReActAgent as OfficialReActAgent

            # Create token counter
            token_counter = SimpleTokenCounter(chars_per_token=4)

            # Use provided values or defaults
            threshold = compression_threshold or self.DEFAULT_COMPRESSION_THRESHOLD
            keep = keep_recent or self.DEFAULT_KEEP_RECENT

            compression_config = OfficialReActAgent.CompressionConfig(
                enable=True,
                agent_token_counter=token_counter,
                trigger_threshold=threshold,
                keep_recent=keep,
                compression_prompt=self.COMPRESSION_PROMPT,
                summary_template=self.SUMMARY_TEMPLATE,
                summary_schema=CompressionSummarySchema,
                compression_model=compression_model,
                compression_formatter=compression_formatter,
            )
            logger.info(
                f"Memory compression enabled: threshold={threshold} tokens, keep_recent={keep}")

        # Initialize parent ReActAgent with toolkit and compression config
        super().__init__(
            name="LocalManus-ReAct",
            sys_prompt="",  # Will be set dynamically for each conversation
            model=model,
            formatter=formatter,
            toolkit=skill_manager.toolkit,
            compression_config=compression_config,
        )
        self.skill_manager = skill_manager
        self.original_model = model  # Keep reference for streaming if needed

    def _build_system_prompt(self, user_context: Optional[Dict] = None) -> str:
        """Build system prompt with current context and tools."""
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_info_str = json.dumps(
            user_context, ensure_ascii=False) if user_context else "Anonymous"
        skills_prompt = self.skill_manager.get_skills_prompt() or ""

        # Get tools metadata from toolkit
        tools_schemas = self.skill_manager.toolkit.get_json_schemas()
        tools_metadata = json.dumps(
            tools_schemas, indent=2, ensure_ascii=False)

        return REACT_AGENT_SYSTEM_PROMPT.format(
            current_time=current_time,
            user_info=user_info_str,
            skills_prompt=skills_prompt,
            tools_metadata=tools_metadata
        )

    async def run_stream(self, messages: list):
        """
        Manual ReAct loop with streaming support.

        Implements: Think → Act → Observe cycle
        - THINK: Stream reasoning content to frontend in real-time
        - ACT: Execute tool calls and notify frontend
        - OBSERVE: Feed tool results back to model

        Repeats until task is complete or max iterations reached.

        Yields:
            Dict[str, Any]: Content chunks with 'content' key, or internal events like '_sync'
        """
        MAX_ITERATIONS = 10
        iteration = 0
        inner_iteration = 0
        new_messages = []

        try:
            # Convert dict messages to Msg objects
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

            # Get the last user message
            last_msg = msg_objects[-1] if msg_objects else None
            if not last_msg:
                yield {"content": "Error: No message to respond to."}
                return

            # Add to agent's memory
            await self.memory.add(last_msg)

            logger.info(f"=== ReAct Iteration {iteration} ===")

            while iteration < MAX_ITERATIONS:
                iteration += 1
                # === STEP 1: THINK (Reasoning) ===
                if iteration == 1:
                    yield {"content": f"\n🧠 **[Thinking... (Iteration {iteration})]**\n\n"}

                # Stream reasoning from model
                reasoning_msg = await self._stream_reasoning()

                # Check if we have tool calls
                tool_calls = self._extract_tool_calls_from_msg(reasoning_msg)

                # Extract and yield text content
                text_content = self._extract_content(reasoning_msg)
                if text_content:
                    yield {"content": text_content}

                if len(tool_calls) == 0:
                    break
                # === REACT LOOP ===
                inner_iteration = 0
                while inner_iteration < len(tool_calls):

                    # === STEP 2: ACT (Tool Execution) ===
                    if not tool_calls:
                        # No more tool calls - task complete
                        logger.info("No tool calls - task complete")
                        break

                    tc = tool_calls[inner_iteration]
                    inner_iteration += 1
                    # Execute each tool call
                    tool_name = tc.get('function', {}).get(
                        'name', tc.get('name', 'unknown'))
                    tool_args = tc.get('function', {}).get('arguments', '{}')

                    # Notify frontend about tool call
                    yield {"content": f"\n\n🔧 **[Tool Call]** `{tool_name}`\n"}
                    if tool_args and tool_args != '{}':
                        try:
                            args_display = json.loads(tool_args) if isinstance(
                                tool_args, str) else tool_args
                            yield {"content": f"```json\n{json.dumps(args_display, indent=2, ensure_ascii=False)}\n```\n"}
                        except:
                            pass

                    # Execute tool
                    yield {"content": "⏳ *Executing...*\n"}

                    try:
                        tool_result = await self._execute_tool(tc)

                        # Yield tool result
                        result_text = self._format_tool_result(tool_result)
                        yield {"content": f"✅ **[Result]**\n{result_text}\n"}

                        # Add tool result to memory for next iteration
                        await self._add_tool_result_to_memory(tc, tool_result)
                    except Exception as e:
                        error_msg = f"❌ **[Error]**: {str(e)}\n"
                        yield {"content": error_msg}
                        await self._add_tool_result_to_memory(tc, f"Error: {str(e)}")

                    # === STEP 3: OBSERVE (Continue Loop) ===
                    # The tool results are now in memory, next iteration will use them
                    yield {"content": "\n---\n"}

                # Store for sync
                new_messages.append(
                    {"role": "assistant", "content": text_content or ""})

        except Exception as e:
            logger.error(f"Error in ReAct loop: {str(e)}", exc_info=True)
            yield {"content": f"\n\n❌ **[Error]**: {str(e)}\n"}

        finally:
            if new_messages:
                yield {"_sync": new_messages}

    async def _stream_reasoning(self) -> Msg:
        """
        Stream reasoning from the model.

        Returns the complete message after streaming.
        """
        from agentscope.agent._react_agent import _MemoryMark

        # Handle plan notebook hints
        if self.plan_notebook:
            hint_msg = await self.plan_notebook.get_current_hint()
            if hint_msg:
                await self.memory.add(hint_msg, marks=_MemoryMark.HINT)

        # Format prompt with system prompt and memory
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                *await self.memory.get_memory(),
            ],
        )

        # Clear hint messages after use
        await self.memory.delete_by_mark(mark=_MemoryMark.HINT)

        # Call model with tools
        res = await self.model(
            prompt,
            tools=self.toolkit.get_json_schemas(),
            tool_choice=None,
        )

        # Process streaming response
        msg = Msg(name=self.name, content=[], role="assistant")

        if self.model.stream:
            # Stream and accumulate content
            async for content_chunk in res:
                msg.content = content_chunk.content
        else:
            # Non-streaming: just use the result
            msg.content = list(res.content) if hasattr(res, 'content') else res

        # Add to memory
        await self.memory.add(msg)

        return msg

    def _extract_tool_calls_from_msg(self, msg: Msg) -> list:
        """Extract tool calls from a message object."""
        tool_calls = []

        if not hasattr(msg, 'content'):
            return tool_calls

        content = msg.content
        if not isinstance(content, list):
            return tool_calls

        for block in content:
            # Object format
            if hasattr(block, 'type') and block.type == 'tool_use':
                tc = {
                    'id': getattr(block, 'id', f'tool_{len(tool_calls)}'),
                    'name': getattr(block, 'name', 'unknown'),
                    'function': {
                        'name': getattr(block, 'name', 'unknown'),
                        'arguments': getattr(block, 'input', '{}')
                    }
                }
                tool_calls.append(tc)
            # Dict format
            elif isinstance(block, dict) and block.get('type') == 'tool_use':
                tc = {
                    'id': block.get('id', f'tool_{len(tool_calls)}'),
                    'name': block.get('name', 'unknown'),
                    'function': {
                        'name': block.get('name', 'unknown'),
                        'arguments': block.get('input', '{}')
                    }
                }
                tool_calls.append(tc)

        return tool_calls

    async def _execute_tool(self, tool_call: Dict) -> Any:
        """Execute a single tool call."""
        # Format for toolkit
        tc_formatted = {
            'id': tool_call.get('id', 'unknown'),
            'name': tool_call.get('name') or tool_call.get('function', {}).get('name', 'unknown'),
            'input': tool_call.get('input') or tool_call.get('function', {}).get('arguments', {})
        }

        # Parse arguments if string
        if isinstance(tc_formatted['input'], str):
            try:
                tc_formatted['input'] = json.loads(tc_formatted['input'])
            except:
                tc_formatted['input'] = {}

        # Execute via toolkit
        from agentscope.message import ToolUseBlock
        tool_block = ToolUseBlock(
            type="tool_use",
            id=tc_formatted['id'],
            name=tc_formatted['name'],
            input=tc_formatted['input']
        )

        # Call tool and collect results
        results = []
        gen = await self.toolkit.call_tool_function(tool_block)
        for response in gen:
            results.append(response)

        return results[0] if len(results) == 1 else results

    def _format_tool_result(self, result: Any) -> str:
        """Format tool result for display."""
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, list):
                texts = []
                for block in content:
                    if hasattr(block, 'text'):
                        texts.append(block.text)
                    elif isinstance(block, dict) and 'text' in block:
                        texts.append(block['text'])
                return '\n'.join(texts)
            return str(content)
        return str(result)

    async def _add_tool_result_to_memory(self, tool_call: Dict, result: Any):
        """Add tool result to agent's memory."""
        from agentscope.message import Msg, ToolResultBlock

        tool_name = tool_call.get('name') or tool_call.get(
            'function', {}).get('name', 'unknown')
        tool_id = tool_call.get('id', 'unknown')

        # Format result as string
        result_str = self._format_tool_result(result)

        # Create tool result message
        result_msg = Msg(
            name="system",
            content=[
                ToolResultBlock(
                    type="tool_result",
                    id=tool_id,
                    name=tool_name,
                    output=result_str,
                )
            ],
            role="system"
        )

        await self.memory.add(result_msg)

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
            name = tool_call.get('function', {}).get(
                'name', tool_call.get('name', 'unknown'))
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
