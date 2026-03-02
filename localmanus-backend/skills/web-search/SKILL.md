---
name: web-search
description: Web search and scraping using the sandbox's Chrome browser via Playwright/CDP. All operations execute in isolated sandbox environment.
---

# Web Search Skill

This skill enables AI agents to search the web and scrape content using a real Chrome browser running inside the sandbox container. Unlike simple HTTP requests, this uses Playwright connected via Chrome DevTools Protocol (CDP) to execute JavaScript, bypass bot detection, and interact with dynamic websites.

## Capabilities

- 🔍 **Web Search** — Search Bing, Google, or DuckDuckGo using sandbox Chrome
- 📄 **Page Scraping** — Extract visible text from any webpage with JS rendering
- 📸 **Screenshots** — Capture page screenshots for visual verification
- ✅ **Status Check** — Verify sandbox browser availability

## Architecture

```
User Request
    ↓
WebSearchSkill
    ↓
SandboxManager → SandboxContainer (Chrome + CDP)
    ↓
Playwright.connect_over_cdp(cdp_url)
    ↓
Real Chrome Browser (isolated, headful)
    ↓
Navigate → Render JS → Extract Content
```

## Requirements

- **Sandbox Mode**: `local` or `online` (configured in `.env`)
- **Sandbox Container**: Must be running (auto-started in `online` mode)
- **Playwright**: Python package installed
- **User ID**: Required for all operations (resolves user's sandbox instance)

## Configuration

```bash
# .env in localmanus-backend/
SANDBOX_MODE=local                    # or 'online'
SANDBOX_LOCAL_URL=http://localhost:8080
USE_CHINA_MIRROR=false
```

## Usage Examples

### Check Browser Status
```python
result = await web_search_skill.check_browser_status(user_id="123")
# Returns: Browser version, CDP URL, sandbox mode, status
```

### Search the Web
```python
# Search Bing (default)
result = await web_search_skill.search_web(
    query="Python asyncio tutorial",
    user_id="123",
    engine="bing",        # Options: bing, google, duckduckgo
    max_results=5
)

# Search Google
result = await web_search_skill.search_web(
    query="machine learning",
    user_id="123",
    engine="google"
)
```

### Scrape Webpage
```python
result = await web_search_skill.scrape_web(
    url="https://example.com",
    user_id="123"
)
# Returns: Visible text content (nav/footer/scripts removed)
```

### Capture Screenshot
```python
result = await web_search_skill.browser_screenshot(
    url="https://example.com",
    user_id="123"
)
# Returns: Base64-encoded PNG screenshot
```

## Methods

### check_browser_status(user_id: str) → ToolResponse
Verify sandbox browser is available and get connection info.

**Parameters:**
- `user_id` (str): User ID to resolve sandbox instance

**Returns:**
- Browser version, CDP URL, sandbox mode, and status

### search_web(query, user_id, engine, max_results) → ToolResponse
Search the web using specified search engine.

**Parameters:**
- `query` (str): Search query string
- `user_id` (str): User ID for sandbox resolution
- `engine` (str): Search engine — `"bing"` (default), `"google"`, or `"duckduckgo"`
- `max_results` (int): Maximum results to return (default: 5)

**Returns:**
- Formatted search results with title, URL, and snippet

### scrape_web(url, user_id) → ToolResponse
Navigate to URL and extract visible page text.

**Parameters:**
- `url` (str): URL to scrape
- `user_id` (str): User ID for sandbox resolution

**Returns:**
- Clean text content (scripts, styles, nav elements removed via JS)

### browser_screenshot(url, user_id) → ToolResponse
Navigate to URL and capture screenshot.

**Parameters:**
- `url` (str): URL to visit
- `user_id` (str): User ID for sandbox resolution

**Returns:**
- Base64-encoded PNG screenshot (truncated in text, full data available)

## Error Handling

All methods return `ToolResponse` with error details:

| Error Type | Cause | Solution |
|------------|-------|----------|
| `SandboxBrowserError` | Sandbox not running | Start sandbox container |
| Connection Error | CDP URL unreachable | Check SANDBOX_LOCAL_URL |
| Timeout | Page load too slow | Retry with simpler URL |

## Technical Implementation

### Browser Connection
- Uses **Playwright** with **CDP** (Chrome DevTools Protocol)
- Browser pool caches connections per CDP URL for efficiency
- Real Chrome instance inside sandbox container (not headless)

### Content Extraction
- JavaScript execution for dynamic content
- DOM cleaning: removes `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`
- Whitespace normalization for readable text

### Search Engine Support
- **Bing**: `https://www.bing.com/search?q={query}`
- **Google**: `https://www.google.com/search?q={query}`
- **DuckDuckGo**: `https://duckduckgo.com/?q={query}`

All engines parsed via BeautifulSoup from rendered HTML.

## Security & Isolation

- ✅ **No host browser used** — All operations in sandbox container
- ✅ **Per-user isolation** — Each user gets separate browser context
- ✅ **Network isolation** — Sandbox container network policies apply
- ✅ **No persistent cookies** — Fresh browser state per session

## Troubleshooting

### "Sandbox browser not available"
```bash
# Start sandbox manually (local mode)
docker run --security-opt seccomp=unconfined \
  --rm -it -p 8080:8080 \
  ghcr.io/agent-infra/sandbox:latest
```

### "Failed to connect to CDP"
- Verify `SANDBOX_LOCAL_URL` matches sandbox container port
- Check firewall rules for port 8080
- Ensure sandbox fully started (wait 5-10 seconds)

### Slow page loads
- Increase timeout in method calls
- Check sandbox container resources (CPU/memory)
- Some sites may block automation — try alternative URLs