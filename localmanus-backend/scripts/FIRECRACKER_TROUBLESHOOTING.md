# Sandbox System - Migration Guide

## Overview

The Firecracker module has been **refactored** to use the [agent-infra/sandbox](https://github.com/agent-infra/sandbox) architecture, which provides:

- **🌐 Browser Automation** - Full Playwright/CDP support with VNC access
- **💻 Development Environment** - VSCode Server, Jupyter, Terminal
- **📁 File Operations** - Complete file system access
- **🔧 MCP Integration** - Model Context Protocol servers
- **🚀 Dual Mode** - Local (shared) or Online (isolated Docker containers)

## Architecture

### Old System (Firecracker VM)
```
FirecrackerManager → VM Process → Unix Socket → Firecracker API
```

### New System (agent-infra/sandbox)
```
SandboxManager → [Local Mode] → HTTP API → Shared Sandbox
                ↓
              [Online Mode] → Docker Container → Isolated Sandbox
```

## Two Modes

### 1. LOCAL Mode (Development/Shared)
- **Connect to**: Existing sandbox at `http://192.168.96.135:8080`
- **Use when**: Development, testing, shared environment
- **Benefits**: No container overhead, instant access, shared resources
- **Limitations**: Shared environment (not isolated per user)

### 2. ONLINE Mode (Production/Isolated)
- **Spin up**: New Docker container per user
- **Use when**: Production, multi-user, isolation required
- **Benefits**: Complete isolation, per-user resources
- **Limitations**: Container startup time (~3s), resource overhead

## Configuration

### Environment Variables (.env)

```bash
# Sandbox Mode: local or online
SANDBOX_MODE=local

# Local sandbox URL (when mode=local)
SANDBOX_LOCAL_URL=http://192.168.96.135:8080

# Use China mirror for Docker images (when mode=online)
USE_CHINA_MIRROR=false
```

### Programmatic Configuration

```python
from core.firecracker_sandbox import SandboxManager, SandboxMode

# Local mode
manager = SandboxManager(
    mode=SandboxMode.LOCAL,
    local_url="http://192.168.96.135:8080"
)

# Online mode
manager = SandboxManager(
    mode=SandboxMode.ONLINE,
    use_china_mirror=False
)
```

## Usage Examples

### Basic Usage (with existing code)

```python
from core.firecracker_sandbox import sandbox_manager

# Get sandbox for user
sandbox_info = sandbox_manager.get_sandbox(user_id="123")

# Execute command
result = sandbox_manager.execute_command("123", "ls -la")
print(result['data']['output'])

# Cleanup (only needed in ONLINE mode)
sandbox_manager.cleanup_sandbox("123")
```

### Using SandboxClient Directly

```python
from core.firecracker_sandbox import SandboxClient

client = SandboxClient("http://192.168.96.135:8080")

# Get context
context = client.get_context()
home_dir = context['data']['home_dir']

# Execute command
result = client.exec_command("pwd && whoami")
print(result['data']['output'])

# File operations
client.write_file(f"{home_dir}/test.txt", "Hello World!")
content = client.read_file(f"{home_dir}/test.txt")
files = client.list_files(home_dir)

# Browser operations
browser_info = client.get_browser_info()
cdp_url = browser_info['data']['cdp_url']
screenshot = client.screenshot()

# Jupyter execution
result = client.execute_jupyter_code("""
import sys
print(f"Python {sys.version}")
""")
```

### Advanced: Playwright Integration

```python
from playwright.async_api import async_playwright
from core.firecracker_sandbox import sandbox_manager

async def browse_with_playwright(user_id: str):
    # Get sandbox
    sandbox_info = sandbox_manager.get_sandbox(user_id)
    client = sandbox_manager.get_client(user_id)
    
    # Get CDP URL
    browser_info = client.get_browser_info()
    cdp_url = browser_info['data']['cdp_url']
    
    # Connect Playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()
        
        await page.goto("https://example.com")
        title = await page.title()
        
        # Take screenshot
        await page.screenshot(path="screenshot.png")
        
        await browser.close()
```

## API Reference

### SandboxManager

| Method | Description |
|--------|-------------|
| `get_sandbox(user_id)` | Get or create sandbox for user |
| `get_client(user_id)` | Get API client for user's sandbox |
| `execute_command(user_id, cmd, cwd)` | Execute shell command |
| `cleanup_sandbox(user_id)` | Stop and remove sandbox (ONLINE mode) |
| `cleanup_all()` | Cleanup all sandboxes |

### SandboxClient

| Method | Description |
|--------|-------------|
| `get_context()` | Get sandbox environment info |
| `exec_command(cmd, cwd)` | Execute shell command |
| `read_file(path)` | Read file content |
| `write_file(path, content)` | Write file |
| `list_files(path)` | List directory contents |
| `screenshot()` | Take browser screenshot |
| `get_browser_info()` | Get CDP URL and browser info |
| `execute_jupyter_code(code)` | Run Python in Jupyter kernel |

### SandboxInfo (Dataclass)

```python
@dataclass
class SandboxInfo:
    sandbox_id: str           # User/sandbox identifier
    base_url: str             # API base URL
    mode: SandboxMode         # LOCAL or ONLINE
    container_id: Optional[str]  # Docker container ID (ONLINE)
    vnc_url: Optional[str]    # VNC web viewer URL
    vscode_url: Optional[str] # VSCode server URL
    home_dir: Optional[str]   # Home directory path
```

## Setup Instructions

### Local Mode Setup

1. **Start local sandbox**:
   ```bash
   docker run --security-opt seccomp=unconfined \
     --rm -it -p 8080:8080 \
     ghcr.io/agent-infra/sandbox:latest
   ```

2. **Configure LocalManus**:
   ```bash
   # In .env
   SANDBOX_MODE=local
   SANDBOX_LOCAL_URL=http://192.168.96.135:8080
   ```

3. **Test connection**:
   ```bash
   python scripts/test_sandbox.py --mode local
   ```

### Online Mode Setup

1. **Ensure Docker is running**:
   ```bash
   docker --version
   ```

2. **Configure LocalManus**:
   ```bash
   # In .env
   SANDBOX_MODE=online
   USE_CHINA_MIRROR=false  # true if in China
   ```

3. **Test**:
   ```bash
   python scripts/test_sandbox.py --mode online
   ```

## Migration Checklist

- [x] Refactor core module to use agent-infra/sandbox API
- [x] Support LOCAL and ONLINE modes
- [x] Add configuration via environment variables
- [x] Create SandboxClient for API interactions
- [x] Update .env.example with new variables
- [x] Create test script for both modes
- [ ] Update orchestrator to use new sandbox manager
- [ ] Update skill execution to use sandbox API
- [ ] Add VNC/VSCode URL exposure in UI
- [ ] Add Playwright integration examples

## Benefits of New System

### vs. Original Firecracker
1. **Easier Setup**: No kernel/rootfs compilation, just Docker
2. **Better Integration**: REST API instead of Unix sockets
3. **More Features**: Browser, VSCode, Jupyter out-of-the-box
4. **Flexibility**: Switch between local and online modes
5. **Community**: Active upstream project with examples

### vs. Simple Sandbox
1. **Isolation**: True container isolation (ONLINE mode)
2. **Browser Support**: Built-in Playwright/CDP
3. **Visual Access**: VNC web viewer for debugging
4. **File Sharing**: Proper file system with home directory

## Troubleshooting

### Cannot connect to local sandbox
```bash
# Check if sandbox is running
curl http://192.168.96.135:8080/v1/sandbox

# Start if not running
docker run --security-opt seccomp=unconfined \
  --rm -it -p 8080:8080 \
  ghcr.io/agent-infra/sandbox:latest
```

### Docker container fails to start (ONLINE mode)
```bash
# Check Docker
docker ps
docker logs localmanus-sandbox-{user_id}

# Clean up stale containers
docker ps -a | grep localmanus-sandbox | awk '{print $1}' | xargs docker rm -f
```

### Port already in use
```bash
# Find process using port
lsof -i :8080

# Kill or use different port
# Modify SANDBOX_LOCAL_URL or let ONLINE mode auto-assign
```

## Resources

- **Upstream Project**: https://github.com/agent-infra/sandbox
- **Documentation**: https://deepwiki.com/agent-infra/sandbox/
- **Examples**: https://github.com/agent-infra/sandbox/tree/main/examples
- **Test Script**: `scripts/test_sandbox.py`

---

**Note**: The old Firecracker socket-based system has been completely replaced. The `firecracker_manager` variable is now an alias for `sandbox_manager` for backward compatibility.
