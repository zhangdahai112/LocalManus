# LocalManus

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)

> 🚀 A local-first AI agent platform with multi-agent orchestration, sandboxed execution, and real-time streaming.

LocalManus brings the power of autonomous AI agents to your local environment. Built with privacy and extensibility in mind, it features a modern React frontend, Python FastAPI backend, and containerized sandbox execution for safe code generation and web automation.

## ✨ Features

### Core Capabilities
- **🤖 Multi-Agent System** — Manager, Planner, and ReAct agents working together via AgentScope
- **💬 Real-time Streaming** — Server-Sent Events (SSE) for live agent responses
- **🔧 Skill System** — Extensible toolkit architecture for custom capabilities
- **📁 File Management** — Upload, manage, and process files with agent context
- **🔐 User Authentication** — JWT-based auth with secure session management

### Sandbox Environment
- **🌐 Browser Automation** — Playwright/CDP integration for web scraping and interaction
- **💻 Code Execution** — Sandboxed shell and Python execution via agent-infra/sandbox
- **🎨 Visual Access** — VNC viewer and VSCode Server for real-time development monitoring
- **📊 Jupyter Integration** — Interactive Python notebooks within sandbox
- **🐳 Dual Mode** — Local (shared) or Online (isolated Docker containers)

### Supported Skills
| Skill | Description |
|-------|-------------|
| `gen-web` | Generate full-stack web projects (Next.js, React, Vue) |
| `web-search` | Search web using sandbox Chrome (Bing, Google, DuckDuckGo) |
| `file-operations` | Read, write, and manage files in sandbox |
| `system-execution` | Execute shell commands and Python code |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Chat UI   │  │   Sidebar   │  │   Project Manager   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / WebSocket / SSE
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Auth      │  │   Skills    │  │   File Upload       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  ReActAgent │  │  Planner    │  │   Manager Agent     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│              Sandbox (agent-infra/sandbox)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Chrome    │  │   VSCode    │  │   Terminal/Jupyter  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python** 3.8+
- **Node.js** 18+
- **Docker** (for sandbox)
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/localmanus.git
cd localmanus
```

### 2. Backend Setup

```bash
cd localmanus-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for web automation)
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### 3. Frontend Setup

```bash
cd localmanus-ui

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your settings
```

### 4. Start Sandbox (Local Mode)

```bash
# Start the sandbox container
docker run --security-opt seccomp=unconfined \
  --rm -it -p 8080:8080 \
  ghcr.io/agent-infra/sandbox:latest
```

### 5. Run Development Servers

```bash
# Terminal 1: Backend
cd localmanus-backend
python main.py

# Terminal 2: Frontend
cd localmanus-ui
npm run dev
```

Access the application at `http://localhost:3000`

## ⚙️ Configuration

### Environment Variables

#### Backend (`localmanus-backend/.env`)

```bash
# LLM Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=http://localhost:11434/v1
MODEL_NAME=gpt-4

# Sandbox Configuration
SANDBOX_MODE=local                    # local or online
SANDBOX_LOCAL_URL=http://localhost:8080
USE_CHINA_MIRROR=false                # true if in China
```

#### Frontend (`localmanus-ui/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Sandbox Modes

| Mode | Use Case | Isolation | Startup |
|------|----------|-----------|---------|
| **Local** | Development, testing | Shared | Instant |
| **Online** | Production, multi-user | Per-user containers | ~3 seconds |

## 🛠️ Development

### Project Structure

```
localmanus/
├── localmanus-backend/          # Python FastAPI backend
│   ├── agents/                  # ReAct, Manager, Planner agents
│   ├── core/                    # Orchestrator, Auth, Config
│   ├── skills/                  # Skill implementations
│   │   ├── gen-web/            # Web project generation
│   │   ├── web-search/         # Browser-based search
│   │   ├── file-operations/    # File management
│   │   └── system-execution/   # Shell/Python execution
│   └── main.py                  # FastAPI entry point
│
├── localmanus-ui/               # Next.js frontend
│   ├── app/                     # App router
│   │   ├── components/         # React components
│   │   ├── projects/           # Project management
│   │   └── settings/           # Settings page
│   └── public/                  # Static assets
│
├── nginx/                       # Nginx configuration
├── docker-compose.yml           # Docker orchestration
└── scripts/                     # Deployment scripts
```

### Adding a New Skill

1. Create skill directory: `localmanus-backend/skills/my-skill/`
2. Implement skill class inheriting from `BaseSkill`
3. Create `SKILL.md` with metadata and documentation
4. Restart backend — skill auto-registers

Example:

```python
from core.skill_manager import BaseSkill
from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

class MySkill(BaseSkill):
    async def my_tool(self, param: str, user_id: str) -> ToolResponse:
        """Tool description for agent."""
        result = f"Processed: {param}"
        return ToolResponse(content=[TextBlock(type="text", text=result)])
```

## 🐳 Docker Deployment

### Local Development with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Deployment

```bash
# Production with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or use deployment scripts
./deploy-production.sh
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed instructions.

## 📚 Documentation

- [Architecture Overview](ARCHITECTURE.md) — System design and component interactions
- [Docker Deployment](DOCKER_DEPLOYMENT.md) — Container orchestration guide
- [Local Development](LOCAL_DEVELOPMENT.md) — Development environment setup
- [Skill Implementation](SKILL_LIBRARY_IMPLEMENTATION.md) — Creating custom skills
- [Sandbox Migration](localmanus-backend/scripts/SANDBOX_MIGRATION_GUIDE.md) — Sandbox architecture

## 🔧 Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check Python version
python --version  # Should be 3.8+

# Verify dependencies
pip install -r requirements.txt --upgrade
```

**Sandbox connection failed**
```bash
# Verify sandbox is running
curl http://localhost:8080/v1/sandbox

# Check Docker
docker ps | grep sandbox
```

**Frontend build errors**
```bash
# Clear Next.js cache
cd localmanus-ui
rm -rf .next
npm run build
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [AgentScope](https://github.com/modelscope/agentscope) — Multi-agent framework
- [agent-infra/sandbox](https://github.com/agent-infra/sandbox) — Browser automation sandbox
- [Next.js](https://nextjs.org/) — React framework
- [FastAPI](https://fastapi.tiangolo.com/) — Python web framework

## 📞 Support

- 📧 Email: support@localmanus.dev
- 💬 Discord: [Join our community](https://discord.gg/localmanus)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/localmanus/issues)

---

<p align="center">
  Made with ❤️ by the LocalManus Team
</p>
