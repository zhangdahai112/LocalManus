---
name: gen-web
description: Generate full-stack web projects using Sandbox environments with browser automation, file operations, and isolated development capabilities.
---

# Gen Web Skill

This skill enables AI agents to generate full-stack web projects in sandbox environments (based on agent-infra/sandbox), providing secure, feature-rich development environments with browser automation, VSCode access, and complete file system operations.

## Capabilities

- 🚀 Generate complete full-stack web projects (Next.js, React, Vue, etc.)
- 💻 Execute shell commands within user-specific sandbox instances
- 📁 Full file system operations (read, write, list files)
- 🌐 Browser automation via Playwright/CDP
- 🎨 VNC visual access for real-time development monitoring
- 💼 VSCode Server integration for code editing
- 📊 Jupyter kernel for Python execution
- 🔧 Development server management
- 🔄 Support for both LOCAL (shared) and ONLINE (isolated) modes

## Usage

When you need to create a new web project, execute commands, or manage files in a sandbox environment, the AI will automatically use this skill. Specify the project name, desired tech stack, and any specific requirements.

Example interactions:
- "Create a Next.js project called 'my-blog' with TypeScript and Tailwind"
- "Run 'npm install react-router-dom' in my project directory"
- "Generate a full-stack e-commerce application with React frontend"
- "Read the package.json file from my project"
- "Start the development server on port 3000"
- "Show me the sandbox environment information"

## Technical Implementation

This skill integrates with:

- **Sandbox Manager** for environment orchestration
- **REST API** for all sandbox interactions
- **Docker** for container-based isolation (ONLINE mode)
- **Browser Automation** via Chrome DevTools Protocol (CDP)
- **VNC Streaming** for visual development environment access
- **File System API** for complete file operations
- **Shell Execution** within sandbox contexts
- **VSCode Server** for in-browser code editing
- **Jupyter Kernel** for Python code execution

The skill creates isolated development environments where users can safely develop, test, and deploy web applications without affecting the host system or other users.

## Operating Modes

### LOCAL Mode (Development)
- Connects to shared sandbox at configured URL
- Instant access, no startup overhead
- Suitable for development and testing
- Shared resources across users

### ONLINE Mode (Production)
- Spins up isolated Docker container per user
- Complete isolation between users
- ~3 second startup time
- Suitable for production multi-user scenarios

## Methods

### create_fullstack_project

Generates a full-stack project inside a sandbox environment.

**Parameters:**
- `project_name` (str): Name of the project
- `tech_stack` (str): Desired tech stack (e.g., 'Next.js', 'React + Express', 'Vue')
- `user_id` (str): The ID of the user (injected by system)

**Returns:**
- ToolResponse: Summary of generated project, file list, and access URLs

**Supported Tech Stacks:**
- Next.js (with TypeScript, Tailwind, App Router)
- React + Vite (with TypeScript)
- Generic npm projects

### run_shell_command

Runs a shell command inside the user's sandbox environment.

**Parameters:**
- `command` (str): The shell command to execute
- `user_id` (str): The ID of the user
- `cwd` (str, optional): Working directory for command execution

**Returns:**
- ToolResponse: Command output with exit code

### read_file

Reads a file from the user's sandbox.

**Parameters:**
- `file_path` (str): Absolute path to the file
- `user_id` (str): The ID of the user

**Returns:**
- ToolResponse: File content

### write_file

Writes content to a file in the user's sandbox.

**Parameters:**
- `file_path` (str): Absolute path to the file
- `content` (str): Content to write
- `user_id` (str): The ID of the user

**Returns:**
- ToolResponse: Success confirmation with file size

### list_files

Lists files in a directory within the user's sandbox.

**Parameters:**
- `directory` (str): Directory path to list
- `user_id` (str): The ID of the user

**Returns:**
- ToolResponse: List of files and directories

### start_dev_server

Starts a development server for a web project.

**Parameters:**
- `project_dir` (str): Project directory path
- `user_id` (str): The ID of the user
- `port` (int, optional): Port to run the server on (default: 3000)

**Returns:**
- ToolResponse: Server status and access information

### get_sandbox_info

Gets information about the user's sandbox environment.

**Parameters:**
- `user_id` (str): The ID of the user

**Returns:**
- ToolResponse: Sandbox information including URLs, mode, and capabilities

## Security Features

- User isolation through sandbox environments
- Docker-based containerization (ONLINE mode)
- Resource limiting and monitoring
- Secure command execution environment
- Network isolation between user environments
- Automatic cleanup of unused resources
- Seccomp security profiles
- File system access controls

## Requirements

### For LOCAL Mode:
- Docker installed and running
- agent-infra/sandbox container running at configured URL
- Access to sandbox API endpoints

### For ONLINE Mode:
- Docker installed and running
- Sufficient system resources for container allocation
- Network connectivity to pull sandbox images

### Common:
- Python 3.8+
- requests library
- Node.js and npm (pre-installed in sandbox)
- Modern web browser for VNC/VSCode access

## Configuration

Set in `.env` file:
```bash
SANDBOX_MODE=local  # or 'online'
SANDBOX_LOCAL_URL=http://192.168.126.131:8080
USE_CHINA_MIRROR=false  # true if in China
```

## Access URLs

Once a sandbox is created, users can access:
- **VNC Browser**: Web-based visual access to sandbox desktop
- **VSCode Server**: In-browser code editor
- **API Docs**: Swagger documentation at `/v1/docs`
- **MCP Services**: Model Context Protocol servers

## Troubleshooting

### Cannot create project
- Ensure sandbox is running and accessible
- Check Docker is running (ONLINE mode)
- Verify network connectivity to sandbox URL

### Command execution fails
- Check command syntax
- Verify working directory exists
- Check sandbox logs for errors

### File operations fail
- Ensure file paths are absolute
- Check file permissions
- Verify home directory is accessible

For more details, see the [Sandbox Migration Guide](../../scripts/SANDBOX_MIGRATION_GUIDE.md).