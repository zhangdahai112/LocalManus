import asyncio
import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus

from core.skill_manager import BaseSkill
from core.firecracker_sandbox import sandbox_manager
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

logger = logging.getLogger("LocalManus-WebSearch")

# Shared Playwright browser pool: cdp_url -> (playwright, browser)
_browser_pool: dict = {}


async def _get_playwright_browser(cdp_url: str):
    """Return a cached Playwright browser connected over CDP, or create one."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "playwright is not installed. Run: pip install playwright && playwright install chromium"
        )

    if cdp_url not in _browser_pool:
        pw = await async_playwright().start()
        browser = await pw.chromium.connect_over_cdp(cdp_url)
        _browser_pool[cdp_url] = (pw, browser)
        logger.info(f"Connected to sandbox browser via CDP: {cdp_url}")

    return _browser_pool[cdp_url][1]


def _get_cdp_url(user_id: str) -> str:
    """Resolve the CDP WebSocket URL for the user's sandbox."""
    client = sandbox_manager.get_client(str(user_id))
    info = client.get_browser_info()
    cdp_url = info.get("data", {}).get("cdp_url") or info.get("cdp_url", "")
    if not cdp_url:
        # Fallback: build from sandbox base URL
        sandbox_info = sandbox_manager.get_sandbox(str(user_id))
        base = sandbox_info.base_url.rstrip("/")
        cdp_url = f"{base}/cdp"
    return cdp_url


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


class WebSearchSkill(BaseSkill):
    """
    Web search and scraping skill powered by the sandbox's Chrome browser.
    Uses Playwright over CDP to drive the real Chromium instance inside the
    agent-infra/sandbox container — bypasses bot-detection that blocks
    simple HTTP clients.
    """

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Search the web and scrape pages using the sandbox Chrome browser."

    # ------------------------------------------------------------------
    # Public tool methods
    # ------------------------------------------------------------------

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
            results = await self._browser_search(query, user_id, engine, max_results)
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
            text = await self._browser_fetch_text(url, user_id)
            return ToolResponse(content=[TextBlock(type="text", text=text)])
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
            import base64
            cdp_url = _get_cdp_url(str(user_id))
            browser = await _get_playwright_browser(cdp_url)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await page.wait_for_timeout(1500)
                png = await page.screenshot(full_page=False)
            finally:
                await page.close()

            b64 = base64.b64encode(png).decode()
            msg = f"Screenshot captured ({len(png)} bytes, base64 truncated): {b64[:200]}..."
            return ToolResponse(content=[TextBlock(type="text", text=msg)])
        except Exception as e:
            logger.error(f"browser_screenshot error: {e}", exc_info=True)
            return ToolResponse(content=[TextBlock(type="text", text=f"Screenshot error: {e}")])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _browser_search(
        self, query: str, user_id: str, engine: str, max_results: int
    ) -> List[dict]:
        """Drive the sandbox Chromium to a search engine and parse SERP."""
        search_urls = {
            "bing": f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}",
            "google": f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}",
            "duckduckgo": f"https://duckduckgo.com/?q={quote_plus(query)}&ia=web",
        }
        url = search_urls.get(engine.lower(), search_urls["bing"])

        cdp_url = _get_cdp_url(str(user_id))
        browser = await _get_playwright_browser(cdp_url)
        page = await browser.new_page()
        results = []
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(1500)   # let JS render
            html = await page.content()

            if engine.lower() == "bing":
                results = _parse_bing_results(html)
            elif engine.lower() == "google":
                results = _parse_google_results(html)
            elif engine.lower() == "duckduckgo":
                results = _parse_ddg_results(html)
            else:
                results = _parse_bing_results(html)
        finally:
            await page.close()

        return results[:max_results]

    async def _browser_fetch_text(self, url: str, user_id: str) -> str:
        """Drive the sandbox Chromium to a URL and extract visible text."""
        cdp_url = _get_cdp_url(str(user_id))
        browser = await _get_playwright_browser(cdp_url)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(1000)
            # Remove nav/footer/script noise via JS
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
# SERP parsers
# ------------------------------------------------------------------

def _parse_google_results(html: str) -> List[dict]:
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
