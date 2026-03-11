#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Product Manager Writer Image Tools for AgentScope

Image generation tools for product manager articles.
Shares the same functionality as wechat-tech-writer.
"""

import sys
from pathlib import Path

# Add wechat-tech-writer to path for import
tech_writer_path = Path(__file__).parent.parent / 'wechat-tech-writer'
if str(tech_writer_path) not in sys.path:
    sys.path.insert(0, str(tech_writer_path))

from wechat_image_tools import WeChatImageGenSkill

from core.skill_manager import BaseSkill
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock
import logging

logger = logging.getLogger("LocalManus-WeChatPMImageGen")


class WeChatPMImageGenSkill(BaseSkill):
    """
    WeChat Product Manager Image Generation Skill.
    
    Specialized for product manager article covers and diagrams.
    """

    def __init__(self):
        super().__init__()
        self.name = "wechat_pm_image_gen"
        self.description = (
            "Generate images for product manager articles using AI APIs."
        )
        self._base_skill = WeChatImageGenSkill()

    async def generate_product_diagram(
        self,
        description: str,
        diagram_type: str = "flowchart",
        output_path: str = "diagram.png",
        api: str = "gemini",
        user_id: str = ""
    ) -> ToolResponse:
        """
        Generate a product diagram or flowchart image.

        Args:
            description (str): Description of the diagram/flowchart.
            diagram_type (str): Type - "flowchart", "architecture", "wireframe", "roadmap".
            output_path (str): Path to save the image.
            api (str): API to use - "gemini" or "dalle".
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Path to the generated diagram.
        """
        type_prompts = {
            "flowchart": "professional flowchart diagram, clean lines, arrows showing flow, business process visualization",
            "architecture": "system architecture diagram, technical components, clean layout, enterprise software style",
            "wireframe": "UI wireframe mockup, mobile app screens, clean design, UX prototype style",
            "roadmap": "product roadmap timeline, milestones visualization, strategic planning chart, professional business style"
        }

        style = type_prompts.get(diagram_type, type_prompts["flowchart"])

        prompt = f"""Create a {diagram_type} diagram for: {description}

Style: {style}

Requirements:
- Clean, professional appearance
- Clear visual hierarchy
- Suitable for business presentation
- No text or labels (add those manually)
- High contrast for readability

Generate a professional diagram image."""

        if api == "dalle":
            return await self._base_skill.generate_image_dalle(
                prompt=prompt,
                output_path=output_path,
                size="1792x1024",
                user_id=user_id
            )
        else:
            return await self._base_skill.generate_image_gemini(
                prompt=prompt,
                output_path=output_path,
                user_id=user_id
            )

    async def generate_product_cover(
        self,
        product_name: str,
        category: str = "tech",
        output_path: str = "cover.png",
        api: str = "gemini",
        user_id: str = ""
    ) -> ToolResponse:
        """
        Generate a product article cover image.

        Args:
            product_name (str): Product name or topic.
            category (str): Product category - "tech", "finance", "health", "education".
            output_path (str): Path to save the cover.
            api (str): API to use - "gemini" or "dalle".
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Path to the generated cover.
        """
        return await self._base_skill.generate_wechat_cover(
            topic=product_name,
            style=category,
            output_path=output_path,
            api=api,
            user_id=user_id
        )

    # Delegate other methods to base skill
    async def generate_image_gemini(self, prompt: str, output_path: str, 
                                     model: str = "gemini-2.0-flash-exp-image-generation",
                                     user_id: str = "") -> ToolResponse:
        return await self._base_skill.generate_image_gemini(prompt, output_path, model, user_id)

    async def generate_image_dalle(self, prompt: str, output_path: str,
                                    model: str = "dall-e-3", size: str = "1792x1024",
                                    quality: str = "standard", proxy: str = None,
                                    user_id: str = "") -> ToolResponse:
        return await self._base_skill.generate_image_dalle(prompt, output_path, model, size, quality, proxy, user_id)

    async def list_available_apis(self, user_id: str = "") -> ToolResponse:
        return await self._base_skill.list_available_apis(user_id)
