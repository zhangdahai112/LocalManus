#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Draft Publisher Tools for AgentScope

Supports uploading cover images and creating draft articles for WeChat Public Accounts.
"""

import os
import json
import time
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from core.skill_manager import BaseSkill
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

logger = logging.getLogger("LocalManus-WeChatPublisher")


class WeChatPublisherSkill(BaseSkill):
    """
    WeChat Draft Publisher Skill.
    
    Supports uploading cover images and creating draft articles
    for WeChat Public Accounts via the WeChat API.
    """

    BASE_URL = "https://api.weixin.qq.com/cgi-bin"
    
    ERROR_CODES = {
        40001: "AppSecret错误或者AppSecret不属于这个AppID",
        40002: "请确保grant_type字段值为client_credential",
        40013: "不合法的AppID，请检查AppID是否正确",
        40125: "无效的appsecret，请检查AppSecret是否正确",
        40164: "调用接口的IP地址不在白名单中",
        41001: "缺少access_token参数",
        42001: "access_token超时，请检查缓存是否正常",
        45009: "接口调用超过限制（每日API调用量已用完）",
        47003: "参数错误，请检查必填字段是否完整",
        48001: "api功能未授权，请确认公众号类型",
        50005: "用户未关注公众号",
        -1: "系统繁忙，请稍后重试"
    }

    def __init__(self):
        super().__init__()
        self.name = "wechat_publisher"
        self.description = (
            "Upload cover images and create draft articles for WeChat Public Accounts."
        )
        self._token_cache: Dict[str, Any] = {}

    def _get_error_message(self, errcode: int) -> str:
        """Get human-readable error message from error code."""
        return self.ERROR_CODES.get(errcode, f"未知错误 (错误码: {errcode})")

    async def _get_access_token(self, appid: str, appsecret: str) -> str:
        """Get access token from WeChat API."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests is required. Run: pip install requests")

        # Check cache
        cache_key = f"{appid}_token"
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if cached.get("expires_at", 0) > time.time():
                return cached["token"]

        # Request new token
        url = f"{self.BASE_URL}/token"
        params = {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": appsecret
        }

        # Run in thread pool for async compatibility
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, params=params, timeout=30)
        )
        
        result = response.json()

        if "errcode" in result and result["errcode"] != 0:
            raise Exception(f"获取access_token失败: {self._get_error_message(result['errcode'])}")

        access_token = result.get("access_token")
        expires_in = result.get("expires_in", 7200)

        # Cache token
        self._token_cache[cache_key] = {
            "token": access_token,
            "expires_at": time.time() + expires_in - 300  # 5 min buffer
        }

        return access_token

    async def upload_cover_image(
        self,
        image_path: str,
        appid: str,
        appsecret: str,
        user_id: str = ""
    ) -> ToolResponse:
        """
        Upload a cover image to WeChat Media Library.

        Args:
            image_path (str): Path to the cover image file (JPG/PNG, max 2MB).
            appid (str): WeChat Public Account AppID.
            appsecret (str): WeChat Public Account AppSecret.
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Media ID of the uploaded image.
        """
        try:
            import requests
        except ImportError:
            return ToolResponse(content=[TextBlock(
                type="text",
                text="❌ Error: requests package is required. Run: pip install requests"
            )])

        try:
            # Validate image file
            image_file = Path(image_path)
            if not image_file.exists():
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text=f"❌ Error: Image file not found: {image_path}"
                )])

            file_size = image_file.stat().st_size
            if file_size > 2 * 1024 * 1024:  # 2MB limit
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text=f"❌ Error: Image file too large ({file_size / 1024 / 1024:.2f}MB). Max size is 2MB."
                )])

            # Get access token
            access_token = await self._get_access_token(appid, appsecret)

            # Upload image
            url = f"{self.BASE_URL}/material/add_material"
            params = {
                "access_token": access_token,
                "type": "thumb"  # Cover image type
            }

            loop = asyncio.get_event_loop()
            
            with open(image_path, 'rb') as f:
                files = {"media": (image_file.name, f, "image/jpeg")}
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(url, params=params, files=files, timeout=60)
                )

            result = response.json()

            if "errcode" in result and result["errcode"] != 0:
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text=f"❌ Upload failed: {self._get_error_message(result['errcode'])}"
                )])

            media_id = result.get("media_id")
            url_result = result.get("url", "")

            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"✅ Cover image uploaded successfully!\n\n"
                     f"📷 Media ID: {media_id}\n"
                     f"🔗 URL: {url_result}\n\n"
                     f"You can use this Media ID when creating draft articles."
            )])

        except Exception as e:
            logger.error(f"upload_cover_image error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"❌ Upload failed: {str(e)}"
            )])

    async def create_draft_article(
        self,
        title: str,
        content: str,
        thumb_media_id: str,
        appid: str,
        appsecret: str,
        author: str = "",
        digest: str = "",
        content_source_url: str = "",
        need_open_comment: int = 0,
        user_id: str = ""
    ) -> ToolResponse:
        """
        Create a draft article in WeChat Public Account.

        Args:
            title (str): Article title (required, max 64 characters).
            content (str): Article content in HTML format (required).
            thumb_media_id (str): Media ID of cover image (required).
            appid (str): WeChat Public Account AppID.
            appsecret (str): WeChat Public Account AppSecret.
            author (str): Article author (optional).
            digest (str): Article summary (optional, max 120 characters).
            content_source_url (str): Original article URL (optional).
            need_open_comment (int): Enable comments - 0 (no) or 1 (yes).
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Media ID of the created draft.
        """
        try:
            import requests
        except ImportError:
            return ToolResponse(content=[TextBlock(
                type="text",
                text="❌ Error: requests package is required. Run: pip install requests"
            )])

        try:
            # Validate inputs
            if len(title) > 64:
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text="❌ Error: Title exceeds 64 characters limit."
                )])

            if len(digest) > 120:
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text="❌ Error: Digest exceeds 120 characters limit."
                )])

            # Get access token
            access_token = await self._get_access_token(appid, appsecret)

            # Prepare article data
            article = {
                "title": title,
                "thumb_media_id": thumb_media_id,
                "author": author,
                "digest": digest,
                "content": content,
                "content_source_url": content_source_url,
                "need_open_comment": need_open_comment
            }

            # Create draft
            url = f"{self.BASE_URL}/draft/add"
            params = {"access_token": access_token}
            data = {"articles": [article]}

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, params=params, json=data, timeout=60)
            )

            result = response.json()

            if "errcode" in result and result["errcode"] != 0:
                return ToolResponse(content=[TextBlock(
                    type="text",
                    text=f"❌ Create draft failed: {self._get_error_message(result['errcode'])}"
                )])

            media_id = result.get("media_id")

            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"✅ Draft article created successfully!\n\n"
                     f"📄 Media ID: {media_id}\n"
                     f"📝 Title: {title}\n"
                     f"👤 Author: {author or 'N/A'}\n\n"
                     f"You can preview and publish this draft in WeChat MP dashboard."
            )])

        except Exception as e:
            logger.error(f"create_draft_article error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"❌ Create draft failed: {str(e)}"
            )])

    async def get_api_status(self, user_id: str = "") -> ToolResponse:
        """
        Check WeChat API connection status.

        Args:
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: API status information.
        """
        status_info = """
📋 **WeChat Draft Publisher - API Status**

This skill supports the following operations:

1. **upload_cover_image** - Upload cover image to WeChat Media Library
   - Required: image_path, appid, appsecret
   - Returns: media_id for use in draft creation

2. **create_draft_article** - Create draft article
   - Required: title, content, thumb_media_id, appid, appsecret
   - Optional: author, digest, content_source_url, need_open_comment
   - Returns: media_id of created draft

**Prerequisites:**
- WeChat Public Account (订阅号 or 服务号)
- AppID and AppSecret from MP dashboard
- Server IP in whitelist (设置与开发 → 基本配置 → IP白名单)

**Rate Limits:**
- Access token: 2000 requests/day
- Draft creation: 100 drafts/day
- Media upload: 500 uploads/day
"""
        return ToolResponse(content=[TextBlock(type="text", text=status_info)])
