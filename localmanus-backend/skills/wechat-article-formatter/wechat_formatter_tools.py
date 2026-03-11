#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeChat Article Formatter Tools for AgentScope

Converts Markdown articles to beautified HTML suitable for WeChat Public Accounts.
"""

import os
import re
import logging
from typing import Optional, Dict
from pathlib import Path

from core.skill_manager import BaseSkill
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

logger = logging.getLogger("LocalManus-WeChatFormatter")


class WeChatFormatterSkill(BaseSkill):
    """
    WeChat Article Formatter Skill.
    
    Converts Markdown articles to beautified HTML with inline styles
    suitable for WeChat Public Accounts.
    """

    def __init__(self):
        super().__init__()
        self.name = "wechat_formatter"
        self.description = (
            "Convert Markdown articles to beautified HTML for WeChat Public Accounts."
        )

    def _load_theme_css(self, theme: str) -> str:
        """Load theme CSS from templates directory."""
        theme_map = {
            'tech': 'tech-theme.css',
            'minimal': 'minimal-theme.css',
            'business': 'business-theme.css'
        }

        if theme not in theme_map:
            raise ValueError(f"Unknown theme: {theme}. Available: {', '.join(theme_map.keys())}")

        css_file = Path(__file__).parent / 'templates' / theme_map[theme]

        if not css_file.exists():
            raise FileNotFoundError(f"Theme CSS file not found: {css_file}")

        with open(css_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_css_to_dict(self, theme_css: str) -> Dict[str, Dict[str, str]]:
        """Parse CSS to dictionary format for inline styles."""
        try:
            import cssutils
            cssutils.log.setLevel(logging.CRITICAL)
        except ImportError:
            raise ImportError("cssutils is required. Run: pip install cssutils")

        css_rules = {}

        # Parse CSS variables
        css_vars = {}
        var_pattern = r'--([a-zA-Z0-9-]+):\s*([^;]+);'
        for match in re.finditer(var_pattern, theme_css):
            var_name = f'--{match.group(1)}'
            var_value = match.group(2).strip()
            css_vars[var_name] = var_value

        # Use cssutils to parse CSS rules
        sheet = cssutils.parseString(theme_css)

        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                selector = rule.selectorText
                styles = {}

                for prop in rule.style:
                    value = prop.value
                    # Replace CSS variables
                    for var_name, var_value in css_vars.items():
                        value = value.replace(f'var({var_name})', var_value)
                    styles[prop.name] = value

                # Handle multiple selectors
                for sel in selector.split(','):
                    sel = sel.strip()
                    if sel not in css_rules:
                        css_rules[sel] = {}
                    css_rules[sel].update(styles)

        return css_rules

    def _apply_inline_styles(self, html: str, css_rules: Dict[str, Dict[str, str]]) -> str:
        """Apply CSS styles inline to HTML tags."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is required. Run: pip install beautifulsoup4")

        soup = BeautifulSoup(html, 'html.parser')

        for selector, styles in css_rules.items():
            # Skip complex selectors
            if any(x in selector for x in [':', '@', '>', '+', '~', '[', '*']):
                continue

            try:
                elements = soup.select(selector)
                for elem in elements:
                    existing_style = elem.get('style', '')
                    style_dict = {}

                    if existing_style:
                        for item in existing_style.split(';'):
                            if ':' in item:
                                key, value = item.split(':', 1)
                                style_dict[key.strip()] = value.strip()

                    for prop, value in styles.items():
                        if prop not in style_dict:
                            style_dict[prop] = value

                    new_style = '; '.join(f'{k}: {v}' for k, v in style_dict.items())
                    elem['style'] = new_style
            except Exception:
                continue

        return str(soup)

    def _enhance_code_blocks(self, html: str) -> str:
        """Enhance code block display."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is required")

        soup = BeautifulSoup(html, 'html.parser')

        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                classes = code.get('class', [])
                language = None
                for cls in classes:
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
                        break

                if language:
                    pre['data-lang'] = language

        return str(soup)

    def _process_images(self, html: str) -> str:
        """Process image tags for WeChat display."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is required")

        soup = BeautifulSoup(html, 'html.parser')

        for img in soup.find_all('img'):
            existing_style = img.get('style', '')
            if 'max-width' not in existing_style:
                style_additions = 'max-width: 100%; height: auto; display: block; margin: 24px auto;'
                img['style'] = f'{existing_style}; {style_additions}' if existing_style else style_additions

        return str(soup)

    def _wrap_html(self, body_content: str, theme_css: str) -> str:
        """Wrap as complete HTML document."""
        css_vars_match = re.search(r':root\s*\{([^}]+)\}', theme_css)
        css_vars = css_vars_match.group(1) if css_vars_match else ''

        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信公众号文章</title>
    <style>
        :root {{
            {css_vars}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            background: #fff;
            padding: 20px;
            max-width: 720px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>'''

        return html_template

    async def convert_markdown_to_html(
        self,
        markdown_text: str,
        theme: str = "tech",
        user_id: str = ""
    ) -> ToolResponse:
        """
        Convert Markdown text to beautified HTML for WeChat Public Accounts.

        Args:
            markdown_text (str): The Markdown content to convert.
            theme (str): Theme style - 'tech' (default), 'minimal', or 'business'.
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: Beautified HTML content ready for WeChat editor.
        """
        try:
            import markdown
        except ImportError:
            return ToolResponse(content=[TextBlock(
                type="text",
                text="❌ Error: markdown package is required. Run: pip install markdown"
            )])

        try:
            # Remove H1 headings (WeChat has separate title input)
            lines = markdown_text.split('\n')
            filtered_lines = []
            for line in lines:
                if line.strip().startswith('# ') and not line.strip().startswith('## '):
                    continue
                filtered_lines.append(line)
            markdown_text = '\n'.join(filtered_lines)

            # Load theme CSS
            theme_css = self._load_theme_css(theme)

            # Configure Markdown extensions
            extensions = [
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
                'markdown.extensions.codehilite',
            ]

            extension_configs = {
                'codehilite': {
                    'linenums': False,
                    'guess_lang': True,
                    'noclasses': True,
                }
            }

            # Convert Markdown to HTML
            md = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)
            html_content = md.convert(markdown_text)

            # Enhance code blocks
            html_content = self._enhance_code_blocks(html_content)

            # Process images
            html_content = self._process_images(html_content)

            # Parse CSS and apply inline styles
            css_rules = self._parse_css_to_dict(theme_css)
            html_content = self._apply_inline_styles(html_content, css_rules)

            # Wrap as complete HTML
            full_html = self._wrap_html(html_content, theme_css)

            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"✅ Markdown converted to HTML successfully!\n\n"
                     f"🎨 Theme: {theme}\n"
                     f"📄 Output length: {len(full_html)} characters\n\n"
                     f"--- HTML Content ---\n\n{full_html}"
            )])

        except Exception as e:
            logger.error(f"convert_markdown_to_html error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(
                type="text",
                text=f"❌ Conversion failed: {str(e)}"
            )])

    async def list_available_themes(self, user_id: str = "") -> ToolResponse:
        """
        List available themes for WeChat article formatting.

        Args:
            user_id (str): User ID (automatically injected).

        Returns:
            ToolResponse: List of available themes with descriptions.
        """
        themes_info = """
📋 **Available Themes for WeChat Article Formatting**

1. **tech** - 科技风主题
   - 蓝紫渐变配色
   - 现代科技感
   - 适合技术文章

2. **minimal** - 简约风主题
   - 黑白灰配色
   - 极简设计
   - 适合各类文章

3. **business** - 商务风主题
   - 深蓝金色配色
   - 专业稳重
   - 适合商务文章

**Usage:**
```
convert_markdown_to_html(markdown_text="...", theme="tech")
```
"""
        return ToolResponse(content=[TextBlock(type="text", text=themes_info)])
