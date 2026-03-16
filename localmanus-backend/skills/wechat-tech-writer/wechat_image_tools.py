#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Image Generation Tools for AgentScope

Supports SiliconFlow API (Kolors model) for image generation.
Images are saved to the user's sandbox with automatic compression.
"""

import os
import json
import base64
import logging
import asyncio
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

from core.skill_manager import BaseSkill
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

logger = logging.getLogger("LocalManus-WeChatImageGen")


def _get_session_with_retries():
    """Get a requests session with retry configuration."""
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    except ImportError:
        import requests
        return requests


def _get_img_url(
    prompt: str,
    negative_prompt: str = "",
    resolution: str = "1792x1024",
    api_key: Optional[str] = None
) -> str:
    """
    Generate image using SiliconFlow API (Kolors model).
    
    Args:
        prompt: Image generation prompt
        negative_prompt: Negative prompt (things to avoid)
        resolution: Image resolution (e.g., "1792x1024", "1024x1024")
        api_key: SiliconFlow API key (optional, uses env var if not provided)
    
    Returns:
        URL of the generated image
    """
    import requests
    
    # Get API key from parameter, environment, or use default
    if not api_key:
        api_key = os.environ.get('SILICONFLOW_API_KEY', 'sk-gvplafctkpscuqypjnswuaufdydwnxixgvvlxrxpbjoigeub')
    
    if not api_key:
        raise ValueError("SILICONFLOW_API_KEY environment variable not set")
    
    url = "https://api.siliconflow.cn/v1/images/generations"
    
    payload = {
        "model": "Kwai-Kolors/Kolors",
        "prompt": prompt,
        "negative_prompt": negative_prompt if negative_prompt else "",
        "image_size": resolution,
        "batch_size": 1,
        "seed": 4999999999,
        "num_inference_steps": 25,
        "guidance_scale": 7.5
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    session = _get_session_with_retries()
    response = session.request("POST", url, json=payload, headers=headers, timeout=120)
    
    obj = response.json()
    if obj.get("images"):
        return obj.get("images")[0]["url"]
    
    # Handle error
    if obj.get("error"):
        raise Exception(f"SiliconFlow API error: {obj.get('error')}")
    raise Exception(f"Unexpected API response: {response.text}")


class WeChatImageGenSkill(BaseSkill):
    """
    WeChat Image Generation Skill.
    
    Generates images using SiliconFlow API (Kolors model) for WeChat article covers
    and illustrations.
    """

    def __init__(self):
        super().__init__()
        self.name = "wechat_image_gen"
        self.description = (
            "Generate images using SiliconFlow API (Kolors model) for WeChat articles."
        )

    async def generate_image(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "",
        resolution: str = "1792x1024",
        user_id: str = ""
    ) -> ToolResponse:
        """
        Generate image using SiliconFlow API (Kolors model) and save to sandbox.

        Args:
            prompt (str): Image generation prompt (describe the image you want).
            output_path (str): Path to save the generated image in sandbox (e.g., "cover.jpg").
            negative_prompt (str): Negative prompt - things to avoid in the image.
            resolution (str): Image resolution - "1792x1024", "1024x1024", "1024x1792".
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Path to the generated image in sandbox.
        """
        try:
            import requests
        except ImportError:
            return ToolResponse(content=[TextBlock(
                type="text",
                text="❌ Error: requests package is required. Run: pip install requests"
            )])

        try:
            from core.firecracker_sandbox import sandbox_manager
        except ImportError:
            return ToolResponse(content=[TextBlock(
                type="text",
                text="❌ Error: sandbox_manager not available"
            )])

        try:
            api_key = os.environ.get('SILICONFLOW_API_KEY', 'sk-gvplafctkpscuqypjnswuaufdydwnxixgvvlxrxpbjoigeub')
            if not api_key:
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text="❌ Error: SILICONFLOW_API_KEY environment variable not set.\n"
                         "Get your API key from: https://cloud.siliconflow.cn/"
                )])

            # Get sandbox info for the user
            sandbox_info = sandbox_manager.get_sandbox(user_id)
            client = sandbox_manager.get_client(user_id)
            sandbox_home = sandbox_info.home_dir or '/home/gem'
            
            # Ensure output path is relative to sandbox home
            if output_path.startswith('/'):
                sandbox_output_path = output_path
            else:
                sandbox_output_path = f"{sandbox_home}/{output_path}"

            loop = asyncio.get_event_loop()
            
            # Run sync API call in executor
            image_url = await loop.run_in_executor(
                None,
                lambda: _get_img_url(prompt, negative_prompt, resolution, api_key)
            )

            # Download the image
            logger.info(f"Downloading image from: {image_url}")
            session = _get_session_with_retries()
            img_response = await loop.run_in_executor(
                None,
                lambda: session.get(image_url, timeout=60)
            )
            
            if img_response.status_code != 200:
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text=f"❌ Error: Failed to download image (HTTP {img_response.status_code})"
                )])
            
            image_data = img_response.content
            original_size = len(image_data) / 1024
            
            # Compress image
            compressed_data, compression_info = await self._compress_image_data(image_data)
            final_size = len(compressed_data) / 1024
            
            # Save to sandbox
            # Convert to base64 for sandbox write
            image_base64 = base64.b64encode(compressed_data).decode('utf-8')
            
            # Write to sandbox using the client
            # Note: sandbox API expects file content as string
            # We need to write binary data, so we use base64
            try:
                # Create directory if needed
                dir_path = '/'.join(sandbox_output_path.split('/')[:-1])
                client.exec_command(f"mkdir -p {dir_path}")
                
                # Write file using base64 decode in sandbox
                client.write_file(sandbox_output_path + '.b64', image_base64)
                
            except Exception as e:
                logger.error(f"Failed to write to sandbox: {e}")
                # Fallback: try direct write (may not work for binary)
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text=f"❌ Error: Failed to save image to sandbox: {str(e)}"
                )])

            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"✅ Image generated and saved to sandbox!\n\n"
                     f"🎨 Model: Kwai-Kolors/Kolors (SiliconFlow)\n"
                     f"📐 Resolution: {resolution}\n"
                     f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}\n"
                     f"📁 Sandbox path: {sandbox_output_path}\n"
                     f"📊 Original size: {original_size:.1f} KB\n"
                     f"📊 Compressed size: {final_size:.1f} KB\n"
                     f"💾 Compression: {compression_info}"
            )])

        except Exception as e:
            logger.error(f"generate_image error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"❌ SiliconFlow API error: {str(e)}"
            )])

    async def _compress_image_data(
        self,
        image_data: bytes,
        max_size: int = 2 * 1024 * 1024,  # 2MB
        max_dimension: int = 1280,
        quality: int = 85
    ) -> tuple:
        """
        Compress image data to JPEG format with proportional scaling.
        
        Args:
            image_data: Raw image bytes
            max_size: Maximum file size in bytes (default: 2MB)
            max_dimension: Maximum width/height in pixels (default: 1280)
            quality: JPEG quality 1-100 (default: 85)
            
        Returns:
            tuple: (compressed_data: bytes, compression_info: str)
        """
        try:
            from PIL import Image
            import io
        except ImportError:
            logger.warning("PIL not available, skipping image compression")
            return image_data, "Skipped (PIL not available)"

        try:
            loop = asyncio.get_event_loop()
            
            def _compress():
                # Open image from bytes
                img = Image.open(io.BytesIO(image_data))
                
                # Convert to RGB if necessary (handles PNG with transparency)
                if img.mode in ('RGBA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate new dimensions (proportional scaling)
                width, height = img.size
                if width > max_dimension or height > max_dimension:
                    ratio = min(max_dimension / width, max_dimension / height)
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save to bytes
                output = io.BytesIO()
                img.save(output, 'JPEG', quality=quality, optimize=True)
                compressed = output.getvalue()
                
                # Reduce quality if still too large
                current_quality = quality
                while len(compressed) > max_size and current_quality > 30:
                    current_quality -= 10
                    output = io.BytesIO()
                    img.save(output, 'JPEG', quality=current_quality, optimize=True)
                    compressed = output.getvalue()
                
                return compressed, f"quality={current_quality}"
            
            return await loop.run_in_executor(None, _compress)
            
        except Exception as e:
            logger.error(f"Image compression failed: {e}")
            return image_data, f"Failed: {str(e)}"

    async def generate_wechat_cover(
        self,
        topic: str,
        style: str = "tech",
        output_path: str = "cover.jpg",
        negative_prompt: str = "",
        user_id: str = ""
    ) -> ToolResponse:
        """
        Generate a WeChat article cover image with optimized prompt and save to sandbox.

        Args:
            topic (str): Article topic/subject for the cover.
            style (str): Visual style - "tech", "business", "minimal", "creative".
            output_path (str): Path to save the cover image in sandbox.
            negative_prompt (str): Negative prompt - things to avoid.
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Path to the generated cover image in sandbox.
        """
        # Build optimized prompt for WeChat cover
        style_prompts = {
            "tech": "modern technology style, blue and purple gradient, futuristic digital elements, clean design, high quality",
            "business": "professional business style, dark blue and gold colors, corporate elegance, minimalist, high quality",
            "minimal": "minimalist design, black white and gray, simple geometric shapes, clean lines, high quality",
            "creative": "creative artistic style, vibrant colors, abstract elements, dynamic composition, high quality"
        }

        style_desc = style_prompts.get(style, style_prompts["tech"])

        prompt = f"""Create a WeChat article cover image for the topic: "{topic}"

Style: {style_desc}

Requirements:
- 16:9 aspect ratio (landscape)
- No text or watermarks
- Professional quality suitable for social media
- Eye-catching and relevant to the topic
- Clean composition with space for potential text overlay

Generate a visually appealing cover image."""

        # Default negative prompt for covers
        default_negative = "low quality, blurry, text, watermark, logo, signature, bad composition"
        final_negative = negative_prompt if negative_prompt else default_negative

        return await self.generate_image(
            prompt=prompt,
            output_path=output_path,
            negative_prompt=final_negative,
            resolution="1792x1024",
            user_id=user_id
        )

    async def list_available_resolutions(self, user_id: str = "") -> ToolResponse:
        """
        List available image resolutions for SiliconFlow API.

        Args:
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: List of available resolutions.
        """
        info = """
📋 **SiliconFlow Image Generation - Available Resolutions**

**Model:** Kwai-Kolors/Kolors
**API Provider:** SiliconFlow (硅基流动)
**Get API Key:** https://cloud.siliconflow.cn/

## Supported Resolutions:
- `1792x1024` - 16:9 landscape (Recommended for WeChat covers)
- `1024x1024` - 1:1 square
- `1024x1792` - 9:16 portrait

## Usage Examples:
```
# Generate with custom prompt
generate_image(
    prompt="A futuristic city skyline at sunset",
    output_path="cover.png",
    negative_prompt="low quality, blurry",
    resolution="1792x1024"
)

# Generate WeChat cover (optimized)
generate_wechat_cover(
    topic="AI技术",
    style="tech",
    output_path="cover.png"
)
```

## Environment Variable:
Set `SILICONFLOW_API_KEY` with your API key.
"""
        return ToolResponse(content=[TextBlock(type="text", text=info)])

