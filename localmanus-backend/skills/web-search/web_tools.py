import asyncio
import logging
import re
import base64
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus

from core.skill_manager import BaseSkill
from core.firecracker_sandbox import sandbox_manager
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

logger = logging.getLogger("LocalManus-WebSearch")


class SandboxBrowserError(Exception):
    """Raised when sandbox browser is not available."""
    pass


def _ensure_sandbox_available(user_id: str) -> None:
    """Verify sandbox is available for the user."""
    try:
        sandbox_info = sandbox_manager.get_sandbox(str(user_id))
        if not sandbox_info or not sandbox_info.base_url:
            raise SandboxBrowserError(
                f"No sandbox available for user {user_id}. "
                "Please ensure sandbox is started (SANDBOX_MODE=local requires "
                "running sandbox container, SANDBOX_MODE=online will auto-create)."
            )
    except Exception as e:
        if isinstance(e, SandboxBrowserError):
            raise
        raise SandboxBrowserError(
            f"Failed to access sandbox for user {user_id}: {e}"
        ) from e


def _get_sandbox_client(user_id: str):
    """Get sandbox API client for user."""
    return sandbox_manager.get_client(str(user_id))


def _clean_text(raw: str, max_len: int = 6000) -> str:
    """Strip blank lines and collapse whitespace in scraped text."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if line:
            lines.append(line)
    return "\n".join(lines)[:max_len]


def _parse_bing_results(html: str) -> List[dict]:
    """Extract title/url/snippet from Bing SERP HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for li in soup.select("li.b_algo"):
        title_el = li.select_one("h2 a")
        snippet_el = li.select_one(".b_caption p, .b_algoSlug")
        if title_el:
            results.append({
                "title": title_el.get_text(strip=True),
                "url": title_el.get("href", ""),
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })
    return results


def _parse_google_results(html: str) -> List[dict]:
    """Extract title/url/snippet from Google SERP HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for div in soup.select("div.tF2Cxc, div.g"):
        title_el = div.select_one("h3")
        link_el = div.select_one("a[href]")
        snippet_el = div.select_one(".VwiC3b, .st, span.aCOpRe")
        if title_el and link_el:
            href = link_el.get("href", "")
            if href.startswith("/url?"):
                m = re.search(r"[?&]q=([^&]+)", href)
                href = m.group(1) if m else href
            results.append({
                "title": title_el.get_text(strip=True),
                "url": href,
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })
    return results


def _parse_ddg_results(html: str) -> List[dict]:
    """Extract title/url/snippet from DuckDuckGo SERP HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for article in soup.select("article[data-testid='result']"):
        title_el = article.select_one("h2 a")
        snippet_el = article.select_one("[data-result='snippet']")
        if title_el:
            results.append({
                "title": title_el.get_text(strip=True),
                "url": title_el.get("href", ""),
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })
    return results


class WebSearchSkill(BaseSkill):
    """
    Web search and scraping skill powered by the sandbox's Chrome browser.
    
    ALL browser operations use the sandbox REST API (/v1/browser/* endpoints).
    No direct Playwright or host-machine browser access.
    
    This ensures:
    - Consistent browser environment across all users
    - Isolation from host machine
    - Simple REST API interface (no WebSocket/CDP management)
    - Bypass of bot-detection via real browser automation
    """

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = (
            "Search the web and scrape pages using the sandbox Chrome browser. "
            "All operations are executed via sandbox REST API."
        )

    # ------------------------------------------------------------------
    # Public tool methods
    # ------------------------------------------------------------------

    async def check_browser_status(self, user_id: str) -> ToolResponse:
        """
        Check if the sandbox browser is available and ready.

        Args:
            user_id (str): User ID used to resolve the sandbox instance.

        Returns:
            ToolResponse: Browser status information.
        """
        try:
            _ensure_sandbox_available(user_id)
            client = _get_sandbox_client(user_id)
            
            # Get browser info via REST API
            info = client.get_browser_info()
            
            # Get sandbox info
            sandbox_info = sandbox_manager.get_sandbox(str(user_id))
            
            status_text = (
                f"✅ Sandbox browser is ready\n\n"
                f"🔧 Browser Info: {info}\n"
                f"📦 Sandbox Mode: {sandbox_info.mode.value}\n"
                f"🏠 Sandbox Base URL: {sandbox_info.base_url}\n\n"
                f"You can now use search_web, scrape_web, and browser_screenshot."
            )
            return ToolResponse(content=[TextBlock(type="text", text=status_text)])
        except SandboxBrowserError as e:
            error_text = (
                f"❌ Sandbox browser not available\n\n"
                f"Error: {e}\n\n"
                f"To fix:\n"
                f"1. Ensure sandbox is running:\n"
                f"   docker run --security-opt seccomp=unconfined -p 8080:8080 ghcr.io/agent-infra/sandbox:latest\n"
                f"2. Check SANDBOX_MODE in .env (local/online)\n"
                f"3. Verify SANDBOX_LOCAL_URL is correct"
            )
            return ToolResponse(content=[TextBlock(type="text", text=error_text)])
        except Exception as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Unexpected error: {e}")])

    async def search_web(
        self,
        query: str,
        user_id: str,
        engine: str = "bing",
        max_results: int = 5,
    ) -> ToolResponse:
        """
        Search the web via the sandbox Chrome browser and return structured results.

        Args:
            query (str): The search query string.
            user_id (str): User ID used to resolve the sandbox instance.
            engine (str): Search engine to use — 'bing' (default), 'google', or 'duckduckgo'.
            max_results (int): Maximum number of results to return (default: 5).

        Returns:
            ToolResponse: Formatted search results.
        """
        try:
            _ensure_sandbox_available(user_id)
            results = await self._api_search(query, user_id, engine, max_results)
            if not results:
                return ToolResponse(content=[TextBlock(type="text", text="No results found.")])

            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r['title']}**")
                lines.append(f"   URL: {r['url']}")
                if r.get("snippet"):
                    lines.append(f"   {r['snippet']}")
                lines.append("")
            return ToolResponse(content=[TextBlock(type="text", text="\n".join(lines))])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"search_web error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Search error: {e}")])

    async def scrape_web(self, url: str, user_id: str) -> ToolResponse:
        """
        Navigate the sandbox browser to a URL and return the visible page text.

        Args:
            url (str): The URL to scrape.
            user_id (str): User ID used to resolve the sandbox instance.

        Returns:
            ToolResponse: Visible text content of the page.
        """
        try:
            _ensure_sandbox_available(user_id)
            text = await self._api_fetch_text(url, user_id)
            return ToolResponse(content=[TextBlock(type="text", text=text)])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"scrape_web error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Scrape error: {e}")])

    async def browser_screenshot(self, url: str, user_id: str) -> ToolResponse:
        """
        Navigate the sandbox browser to a URL and capture a screenshot.

        Args:
            url (str): The URL to visit.
            user_id (str): User ID used to resolve the sandbox instance.

        Returns:
            ToolResponse: Screenshot saved path or base64 description.
        """
        try:
            _ensure_sandbox_available(user_id)
            client = _get_sandbox_client(user_id)
            
            # Navigate to URL first
            client.browser_navigate(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait a bit for page to stabilize
            await asyncio.sleep(1.5)
            
            # Take screenshot via REST API
            png_bytes = client.screenshot()
            
            b64 = base64.b64encode(png_bytes).decode()
            msg = f"Screenshot captured ({len(png_bytes)} bytes, base64 truncated): {b64[:200]}..."
            return ToolResponse(content=[TextBlock(type="text", text=msg)])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"browser_screenshot error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Screenshot error: {e}")])

    async def browser_click(self, user_id: str, selector: str) -> ToolResponse:
        """
        Click an element in the sandbox browser.

        Args:
            user_id (str): User ID used to resolve the sandbox instance.
            selector (str): CSS selector or XPath of element to click.

        Returns:
            ToolResponse: Click result.
        """
        try:
            _ensure_sandbox_available(user_id)
            client = _get_sandbox_client(user_id)
            
            result = client.browser_execute_action("click", selector=selector)
            return ToolResponse(content=[TextBlock(type="text", text=f"Clicked element: {selector}")])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"browser_click error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Click error: {e}")])

    async def browser_type(self, user_id: str, selector: str, text: str) -> ToolResponse:
        """
        Type text into an element in the sandbox browser.

        Args:
            user_id (str): User ID used to resolve the sandbox instance.
            selector (str): CSS selector or XPath of input element.
            text (str): Text to type.

        Returns:
            ToolResponse: Type result.
        """
        try:
            _ensure_sandbox_available(user_id)
            client = _get_sandbox_client(user_id)
            
            result = client.browser_execute_action("type", selector=selector, text=text)
            return ToolResponse(content=[TextBlock(type="text", text=f"Typed text into: {selector}")])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"browser_type error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Type error: {e}")])

    # ------------------------------------------------------------------
    # Internal helpers using Sandbox REST API
    # ------------------------------------------------------------------

    async def _api_search(
        self, query: str, user_id: str, engine: str, max_results: int
    ) -> List[dict]:
        """Search using sandbox browser via REST API."""
        search_urls = {
            "bing": f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}",
            "google": f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}",
            "duckduckgo": f"https://duckduckgo.com/?q={quote_plus(query)}&ia=web",
        }
        url = search_urls.get(engine.lower(), search_urls["bing"])

        client = _get_sandbox_client(user_id)
        
        # Navigate to search URL
        client.browser_navigate(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for JS to render
        await asyncio.sleep(1.5)
        
        # Get page content
        html = client.browser_get_content()

        # Parse results
        if engine.lower() == "bing":
            results = _parse_bing_results(html)
        elif engine.lower() == "google":
            results = _parse_google_results(html)
        elif engine.lower() == "duckduckgo":
            results = _parse_ddg_results(html)
        else:
            results = _parse_bing_results(html)

        return results[:max_results]

    async def _api_fetch_text(self, url: str, user_id: str) -> str:
        """Fetch page text using sandbox browser via REST API."""
        client = _get_sandbox_client(user_id)
        
        # Navigate to URL
        client.browser_navigate(url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for page to load
        await asyncio.sleep(1.0)
        
        # Execute JS to clean and extract text
        script = """
            () => {
                const remove = ['script','style','nav','footer','header','aside'];
                remove.forEach(tag => document.querySelectorAll(tag).forEach(el => el.remove()));
                return document.body ? document.body.innerText : '';
            }
        """
        result = client.browser_evaluate(script)
        raw_text = result.get('data', {}).get('result', '')
        
        return _clean_text(raw_text)


# ------------------------------------------------------------------
# Legacy shim
# ------------------------------------------------------------------

class WebTools(BaseSkill):
    """
    Legacy class — kept for backward compatibility.
    All methods delegate to WebSearchSkill.
    Note: methods are now async; sync callers should use asyncio.run().
    """

    def __init__(self):
        super().__init__()
        self._skill = WebSearchSkill()

    async def search(
        self, query: str, user_id: str, max_results: int = 5
    ) -> ToolResponse:
        """
        Searches the web using the sandbox browser and returns results.

        Args:
            query (str): The search query string.
            user_id (str): The user ID for sandbox resolution.
            max_results (int): Maximum number of results (default: 5).

        Returns:
            ToolResponse: Formatted search results.
        """
        return await self._skill.search_web(query, user_id, max_results=max_results)

    async def scrape(self, url: str, user_id: str) -> ToolResponse:
        """
        Fetches and returns the visible text content of a webpage.

        Args:
            url (str): The URL to scrape.
            user_id (str): The user ID for sandbox resolution.

        Returns:
            ToolResponse: Scraped text content.
        """
        return await self._skill.scrape_web(url, user_id)
