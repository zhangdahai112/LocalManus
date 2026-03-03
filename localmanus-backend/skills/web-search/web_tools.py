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

# Shared Playwright browser pool: cdp_url -> (playwright, browser)
_browser_pool: dict = {}


class SandboxBrowserError(Exception):
    """Raised when sandbox browser is not available."""
    pass


async def _get_playwright_browser(cdp_url: str):
    """
    Return a cached Playwright browser connected over CDP, or create one.
    
    The cdp_url should be the WebSocket URL exposed by the sandbox container
    (e.g., ws://localhost:8080/cdp or the internal container CDP endpoint).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:
        raise SandboxBrowserError(
            "playwright is not installed. Run: pip install playwright && playwright install chromium"
        ) from e

    if cdp_url not in _browser_pool:
        try:
            pw = await async_playwright().start()
            # Connect to the browser using the container's exposed CDP WebSocket URL
            browser = await pw.chromium.connect_over_cdp(cdp_url)
            _browser_pool[cdp_url] = (pw, browser)
            logger.info(f"Connected to sandbox browser via container CDP: {cdp_url}")
        except Exception as e:
            raise SandboxBrowserError(
                f"Failed to connect to sandbox browser at CDP URL: {cdp_url}. "
                "Ensure sandbox container is running and browser CDP endpoint is accessible. "
                f"Error: {e}"
            ) from e

    return _browser_pool[cdp_url][1]


def _get_cdp_url(user_id: str) -> str:
    """
    Resolve the CDP WebSocket URL for the user's sandbox.
    
    First tries to get the CDP URL from the container's browser info API,
    then falls back to constructing it from the sandbox base URL.
    """
    try:
        client = sandbox_manager.get_client(str(user_id))
        info = client.get_browser_info()
        
        # Try to get CDP URL from container's browser info response
        cdp_url = info.get("data", {}).get("cdp_url") or info.get("cdp_url", "")
        
        if not cdp_url:
            # Fallback: construct CDP URL from sandbox base URL
            # The container exposes CDP at /cdp endpoint
            sandbox_info = sandbox_manager.get_sandbox(str(user_id))
            base = sandbox_info.base_url.rstrip("/")
            # Convert http:// to ws:// for WebSocket connection
            if base.startswith("http://"):
                cdp_url = base.replace("http://", "ws://") + "/cdp"
            elif base.startswith("https://"):
                cdp_url = base.replace("https://", "wss://") + "/cdp"
            else:
                cdp_url = f"ws://{base}/cdp"
        
        logger.debug(f"Resolved CDP URL for user {user_id}: {cdp_url}")
        return cdp_url
        
    except Exception as e:
        raise SandboxBrowserError(
            f"Cannot get browser CDP URL for user {user_id}. "
            "Ensure sandbox container is running and browser CDP endpoint is exposed. "
            f"Error: {e}"
        ) from e


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


def _parse_baidu_results(html: str) -> List[dict]:
    """Extract title/url/snippet from Baidu SERP HTML."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    # Baidu search results are in containers with class 'result' or 'c-container'
    for container in soup.select(".result, .c-container"):
        # Title is typically in h3 with class 't' or within a[href]
        title_el = container.select_one("h3.t a, .t a, h3 a")
        
        # URL is in the title link or in a separate cite element
        url_el = container.select_one("cite, .g, .site")
        
        # Snippet/content is typically in a div with class 'content-right' or 'c-abstract'
        snippet_el = container.select_one(".content-right, .c-abstract, .content-left")
        
        if title_el:
            # Get URL from href or text
            url = title_el.get("href", "")
            if not url and url_el:
                url = url_el.get_text(strip=True)
            
            results.append({
                "title": title_el.get_text(strip=True),
                "url": url,
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })
    
    return results


class WebSearchSkill(BaseSkill):
    """
    Web search and scraping skill powered by the sandbox's Chrome browser.
    
    ALL browser operations use Playwright connected via Chrome DevTools Protocol (CDP)
    to the sandbox's browser, as shown in the agent-infra/sandbox GitHub examples.
    
    This approach:
    - Uses CDP WebSocket connection (not REST API)
    - Supports full browser automation (navigate, click, type, scroll, screenshot)
    - Bypasses bot-detection via real browser automation
    - Maintains browser state across operations
    """

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = (
            "Search the web and scrape pages using the sandbox Chrome browser "
            "via Playwright/CDP connection."
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
            
            # Get CDP URL and connect via Playwright
            cdp_url = _get_cdp_url(str(user_id))
            browser = await _get_playwright_browser(cdp_url)
            
            # Get browser version
            version = await browser.version()
            
            # Get sandbox info
            sandbox_info = sandbox_manager.get_sandbox(str(user_id))
            
            status_text = (
                f"✅ Sandbox browser is ready\n\n"
                f"🌐 CDP URL: {cdp_url}\n"
                f"🔧 Browser Version: {version}\n"
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
            engine (str): Search engine to use — 'bing' (default), 'google', 'duckduckgo', or 'baidu'.
            max_results (int): Maximum number of results to return (default: 5).

        Returns:
            ToolResponse: Formatted search results.
        """
        try:
            _ensure_sandbox_available(user_id)
            results = await self._cdp_search(query, user_id, engine, max_results)
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
            text = await self._cdp_fetch_text(url, user_id)
            return ToolResponse(content=[TextBlock(type="text", text=text)])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"scrape_web error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Scrape error: {e}")])

    async def browser_screenshot(self, url: Optional[str] = None, user_id: str = "") -> ToolResponse:
        """
        Capture a screenshot of the current browser page or navigate to URL first.

        Args:
            url (str, optional): The URL to navigate to before screenshot. If None, screenshots current page.
            user_id (str): User ID used to resolve the sandbox instance.

        Returns:
            ToolResponse: Screenshot in base64 format.
        """
        try:
            _ensure_sandbox_available(user_id)
            
            # Get CDP URL and connect via Playwright
            cdp_url = _get_cdp_url(str(user_id))
            browser = await _get_playwright_browser(cdp_url)
            page = await browser.new_page()
            
            try:
                # Navigate to URL if provided
                if url:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(1.5)
                
                # Take screenshot
                png = await page.screenshot(full_page=False)
            finally:
                await page.close()
            
            b64 = base64.b64encode(png).decode()
            msg = f"Screenshot captured ({len(png)} bytes, base64 truncated): {b64[:200]}..."
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

    async def browser_scroll(self, user_id: str, direction: str = "down", amount: int = 500) -> ToolResponse:
        """
        Scroll the browser page.

        Args:
            user_id (str): User ID used to resolve the sandbox instance.
            direction (str): Scroll direction — 'down' or 'up' (default: 'down').
            amount (int): Pixels to scroll (default: 500).

        Returns:
            ToolResponse: Scroll result.
        """
        try:
            _ensure_sandbox_available(user_id)
            client = _get_sandbox_client(user_id)
            
            result = client.browser_execute_action("scroll", direction=direction, amount=amount)
            return ToolResponse(content=[TextBlock(type="text", text=f"Scrolled {direction} by {amount}px")])
        except SandboxBrowserError as e:
            return ToolResponse(content=[TextBlock(type="text", text=f"❌ Sandbox Error: {e}")])
        except Exception as e:
            logger.error(f"browser_scroll error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Scroll error: {e}")])

    # ------------------------------------------------------------------
    # Internal helpers using Playwright/CDP (as per GitHub examples)
    # ------------------------------------------------------------------

    async def _cdp_search(
        self, query: str, user_id: str, engine: str, max_results: int
    ) -> List[dict]:
        """Search using sandbox browser via Playwright/CDP (as shown in GitHub examples)."""
        search_urls = {
            "bing": f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}",
            "google": f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}",
            "duckduckgo": f"https://duckduckgo.com/?q={quote_plus(query)}&ia=web",
            "baidu": f"https://www.baidu.com/s?wd={quote_plus(query)}&rn={max_results}",
        }
        url = search_urls.get(engine.lower(), search_urls["bing"])

        # Get CDP URL and connect via Playwright (as per GitHub example)
        cdp_url = _get_cdp_url(str(user_id))
        browser = await _get_playwright_browser(cdp_url)
        page = await browser.new_page()
        
        results = []
        try:
            # Navigate and wait for load
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)  # Let JS render
            
            # Get page content
            html = await page.content()

            # Parse results
            if engine.lower() == "bing":
                results = _parse_bing_results(html)
            elif engine.lower() == "google":
                results = _parse_google_results(html)
            elif engine.lower() == "duckduckgo":
                results = _parse_ddg_results(html)
            elif engine.lower() == "baidu":
                results = _parse_baidu_results(html)
            else:
                results = _parse_bing_results(html)
        finally:
            await page.close()

        return results[:max_results]

    async def _cdp_fetch_text(self, url: str, user_id: str) -> str:
        """Fetch page text using sandbox browser via Playwright/CDP."""
        # Get CDP URL and connect via Playwright
        cdp_url = _get_cdp_url(str(user_id))
        browser = await _get_playwright_browser(cdp_url)
        page = await browser.new_page()
        
        try:
            # Navigate and wait for load
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            
            # Execute JS to clean and extract text
            raw = await page.evaluate("""
                () => {
                    const remove = ['script','style','nav','footer','header','aside'];
                    remove.forEach(tag => document.querySelectorAll(tag).forEach(el => el.remove()));
                    return document.body ? document.body.innerText : '';
                }
            """)
        finally:
            await page.close()
        
        return _clean_text(raw)


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
