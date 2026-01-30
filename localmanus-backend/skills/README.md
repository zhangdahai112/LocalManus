# Skills Documentation

This directory contains standardized skill implementations for the LocalManus system following the ComposioHQ awesome-claude-skills pattern. Skills are organized in a folder-based structure with SKILL.md files, compatible with Claude's skill system.

## ComposioHQ-Style Skill Structure

Skills in this directory follow the ComposioHQ awesome-claude-skills pattern with two types of skills:

### 1. Folder-Based Skills (Recommended)

Each folder-based skill follows this structure:
```
skill-folder-name/
├── SKILL.md
└── [optional supporting files]
```

The `SKILL.md` file follows this format:
```markdown
---
name: skill-name
description: Brief description of what this skill does.
---

# Skill Name

Detailed description of the skill.

## Capabilities

- Capability 1
- Capability 2

## Usage

Instructions for how Claude should use this skill.

## Technical Implementation

Details about the underlying technology.
```

### 2. Python-Based Skills (Legacy Support)

For backward compatibility, traditional Python-based skills are still supported:
```python
from core.skill_manager import BaseSkill

class [SkillName]Skill(BaseSkill):
    """
    [Purpose of the skill].
    """

    def __init__(self):
        super().__init__()
        self.name = "[skill_identifier]"
        self.description = "Description of what this skill does."

    def [action_method](self, param1: type, param2: type = default) -> str:
        """
        Brief description of what the method does.

        Args:
            param1 (type): Description of the first parameter
            param2 (type): Description of the second parameter with default value

        Returns:
            str: Description of what is returned
        """
        # Implementation here
        pass
```

## Current Skills

### Folder-Based Skills

#### 1. Web Search Skill
- **Folder**: `web-search/`
- **Name**: `web-search`
- **Purpose**: Web-related operations like searching and scraping
- **Capabilities**: Search the web using DuckDuckGo, scrape text content from web pages

#### 2. System Execution Skill
- **Folder**: `system-execution/`
- **Name**: `system-execution`
- **Purpose**: System operations including code execution and shell commands
- **Capabilities**: Execute Python code snippets, run shell commands

#### 3. File Operations Skill
- **Folder**: `file-operations/`
- **Name**: `file-operations`
- **Purpose**: Basic file operations including read, write, and list
- **Capabilities**: Read content from files, write content to files, list directory contents

### Legacy Python-Based Skills (Maintained for Backward Compatibility)

- `WebTools` and `WebSearchSkill`
- `SystemTools` and `SystemExecutionSkill`
- `FileOps` and `FileOperationSkill`

## Adding New Skills

### To Add a Folder-Based Skill:

1. Create a new folder in the `skills/` directory with a descriptive name
2. Create a `SKILL.md` file in the folder with proper YAML frontmatter
3. The skill will be automatically loaded by the SkillManager

### To Add a Python-Based Skill:

1. Follow the Python-based skill template above
2. Ensure all methods have proper documentation with Args and Returns sections
3. Include type hints for all parameters
4. The skill will be automatically loaded by the SkillManager

## Registration

Skills are automatically registered through the `SkillManager` which:
- Loads Python-based skills from `.py` files
- Loads folder-based skills from directories containing `SKILL.md` files
- Generates appropriate interfaces based on the skill type