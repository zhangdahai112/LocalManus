"""Moonshot-compatible OpenAI Chat Formatter.

Moonshot API (Kimi) with thinking mode enabled requires that:
1. Assistant messages with tool_calls must include `reasoning_content` field
   containing the thinking/reasoning text.
2. The `thinking` content blocks must NOT be dropped but converted to
   `reasoning_content` in the OpenAI-format message dict.

This formatter extends OpenAIChatFormatter to handle these requirements.
"""
import json
from typing import Any

from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg
from agentscope._logging import logger


class MoonshotChatFormatter(OpenAIChatFormatter):
    """OpenAI Chat Formatter with Moonshot thinking mode support.

    When the model has 'thinking' mode enabled, the API requires that
    any assistant message which contains tool_calls also includes a
    `reasoning_content` field with the thinking/reasoning text.

    This formatter extracts `thinking` blocks from assistant messages
    and adds them as `reasoning_content` in the formatted output.
    """

    async def _format(
        self,
        msgs: list[Msg],
    ) -> list[dict[str, Any]]:
        """Format messages, preserving thinking blocks as reasoning_content.

        For assistant messages that contain both `thinking` blocks and
        `tool_use` blocks, the thinking text is extracted and set as
        `reasoning_content` in the formatted message dict.
        """
        self.assert_list_of_msgs(msgs)

        messages: list[dict] = []
        i = 0
        while i < len(msgs):
            msg = msgs[i]
            content_blocks = []
            tool_calls = []
            thinking_texts = []  # Collect thinking content

            for block in msg.get_content_blocks():
                typ = block.get("type")

                if typ == "thinking":
                    # Extract thinking text instead of skipping
                    # ThinkingBlock uses 'thinking' field (not 'text')
                    text = block.get("thinking", "") or block.get("text", "")
                    if text:
                        thinking_texts.append(text)

                elif typ == "text":
                    content_blocks.append({**block})

                elif typ == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id"),
                            "type": "function",
                            "function": {
                                "name": block.get("name"),
                                "arguments": json.dumps(
                                    block.get("input", {}),
                                    ensure_ascii=False,
                                ),
                            },
                        },
                    )

                elif typ == "tool_result":
                    (
                        textual_output,
                        multimodal_data,
                    ) = self.convert_tool_result_to_string(block["output"])

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("id"),
                            "content": textual_output,
                            "name": block.get("name"),
                        },
                    )

                elif typ == "image":
                    from agentscope.formatter._openai_formatter import (
                        _format_openai_image_block,
                    )
                    content_blocks.append(
                        _format_openai_image_block(block)
                    )

                elif typ == "audio":
                    # Filter out audio content from assistant messages
                    if msg.role == "assistant":
                        continue
                    from agentscope.formatter._openai_formatter import (
                        _to_openai_audio_data,
                    )
                    input_audio = _to_openai_audio_data(block["source"])
                    content_blocks.append(
                        {
                            "type": "input_audio",
                            "input_audio": input_audio,
                        },
                    )

                else:
                    logger.warning(
                        "Unsupported block type %s in the message, skipped.",
                        typ,
                    )

            msg_openai: dict[str, Any] = {
                "role": msg.role,
                "name": msg.name,
                "content": content_blocks or None,
            }

            if tool_calls:
                msg_openai["tool_calls"] = tool_calls

            # For Moonshot API: inject reasoning_content when thinking blocks
            # exist alongside tool_calls (required by Moonshot's thinking mode)
            if thinking_texts and tool_calls:
                msg_openai["reasoning_content"] = "\n".join(thinking_texts)

            # When both content and tool_calls are None, skip
            if msg_openai["content"] or msg_openai.get("tool_calls"):
                messages.append(msg_openai)

            i += 1

        return messages
