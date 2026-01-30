---
name: gen-web
description: Generate full-stack web projects using Firecracker microVMs with isolated development environments.
---

# Gen Web Skill

This skill enables Claude to generate full-stack web projects in isolated Firecracker microVMs, providing each user with a secure, high-performance development environment.

## Capabilities

- Generate complete full-stack web projects in isolated VM environments
- Execute shell commands within user-specific Firecracker instances
- Provide VNC visual stream access to development environments
- Manage isolated development sandboxes per user
- Support various tech stacks through customizable project templates

## Usage

When you need to create a new web project or execute commands in a secure VM environment, Claude will automatically use this skill. Specify the project name, desired tech stack, and any specific requirements.

Example interactions:
- "Create a Next.js + FastAPI project called 'my-blog'"
- "Run 'npm install react-router-dom' in my project VM"
- "Generate a full-stack e-commerce application"

## Technical Implementation

This skill integrates with:

- Firecracker microVM manager for lightweight virtualization
- User-specific VM isolation for security
- VNC streaming for visual development environment access
- Shell command execution within VM contexts
- Automatic VM lifecycle management

The skill creates isolated development environments where users can safely develop, test, and deploy web applications without affecting the host system or other users.

## Methods

### create_fullstack_project

Generates a full-stack project inside a Firecracker MicroVM.

**Parameters:**
- `project_name` (str): Name of the project
- `tech_stack` (str): Desired tech stack (e.g., 'Next.js + FastAPI')
- `user_id` (str): The ID of the user (injected by system)

**Returns:**
- `str`: Summary of the generated project and VNC connection info

### run_shell_command

Runs a shell command inside the user's Firecracker VM.

**Parameters:**
- `command` (str): The shell command to execute
- `user_id` (str): The ID of the user

**Returns:**
- `str`: Command output or error message

## Security Features

- User isolation through dedicated VM instances
- Resource limiting and monitoring
- Secure command execution environment
- Network isolation between user environments
- Automatic cleanup of unused VM resources

## Requirements

- Firecracker hypervisor installed and configured
- Proper VM image templates for different tech stacks
- VNC server configuration for visual access
- Sufficient system resources for VM allocation