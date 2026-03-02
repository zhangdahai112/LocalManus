# Sandbox System - Quick Start

## 🚀 30-Second Setup

### Local Mode (Recommended for Development)

```bash
# 1. Start sandbox container (in separate terminal)
docker run --security-opt seccomp=unconfined \
  --rm -it -p 8080:8080 \
  ghcr.io/agent-infra/sandbox:latest

# 2. Configure LocalManus
echo "SANDBOX_MODE=local" >> .env
echo "SANDBOX_LOCAL_URL=http://localhost:8080" >> .env

# 3. Test
python scripts/test_sandbox.py --mode local
```

### Online Mode (Production with Isolation)

```bash
# 1. Ensure Docker is running
docker ps

# 2. Configure LocalManus
echo "SANDBOX_MODE=online" >> .env

# 3. Test (will auto-create containers)
python scripts/test_sandbox.py --mode online
```

## 📝 Quick Code Examples

### Execute Command
```python
from core.firecracker_sandbox import sandbox_manager

result = sandbox_manager.execute_command("user123", "npm --version")
print(result['data']['output'])
```

### File Operations
```python
from core.firecracker_sandbox import sandbox_manager

client = sandbox_manager.get_client("user123")
sandbox_info = sandbox_manager.get_sandbox("user123")

# Write
client.write_file(f"{sandbox_info.home_dir}/app.js", "console.log('Hello');")

# Read
content = client.read_file(f"{sandbox_info.home_dir}/app.js")
```

### Browser Automation
```python
from playwright.async_api import async_playwright

client = sandbox_manager.get_client("user123")
browser_info = client.get_browser_info()
cdp_url = browser_info['data']['cdp_url']

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(cdp_url)
    page = await browser.new_page()
    await page.goto("https://example.com")
```

## 🔧 Configuration Matrix

| Mode | Setup Time | Isolation | Resource | Use Case |
|------|------------|-----------|----------|----------|
| **LOCAL** | Instant | Shared | Low | Development, Testing |
| **ONLINE** | ~3s | Per-user | Medium | Production, Multi-user |

## 🌐 Access URLs (after sandbox starts)

- **API Docs**: http://localhost:8080/v1/docs
- **VNC Browser**: http://localhost:8080/vnc/index.html?autoconnect=true
- **VSCode**: http://localhost:8080/code-server/
- **MCP Services**: http://localhost:8080/mcp

## 🐛 Troubleshooting One-Liners

```bash
# Test local connection
curl http://localhost:8080/v1/sandbox

# List running sandboxes (online mode)
docker ps | grep localmanus-sandbox

# Clean up all sandbox containers
docker ps -a | grep localmanus-sandbox | awk '{print $1}' | xargs docker rm -f

# View sandbox logs
docker logs localmanus-sandbox-{user_id}
```

## 📚 Full Documentation

See [SANDBOX_MIGRATION_GUIDE.md](./SANDBOX_MIGRATION_GUIDE.md) for complete documentation.

## 🔗 Resources

- **GitHub**: https://github.com/agent-infra/sandbox
- **Test Script**: `python scripts/test_sandbox.py`
- **Examples**: https://github.com/agent-infra/sandbox/tree/main/examples
