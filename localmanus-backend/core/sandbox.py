import logging
from typing import Dict, Any

logger = logging.getLogger("LocalManus-Sandbox")

# Delegate to the unified SandboxManager in firecracker_sandbox
# This file is kept for backward compatibility only
from core.firecracker_sandbox import sandbox_manager, SandboxManager, SandboxMode, SandboxClient, SandboxInfo


class LegacySandboxAdapter:
    """
    Thin adapter that wraps sandbox_manager and normalises return values
    to the old {stdout, stderr, exit_code} dict format expected by any
    code that still imports from core.sandbox directly.
    """

    def create_sandbox(self, user_id: str) -> str:
        """Returns home_dir of the user sandbox."""
        info = sandbox_manager.get_sandbox(str(user_id))
        return info.home_dir or "/home/gem"

    def execute_command(self, user_id: str, command: str, cwd: str = None) -> Dict[str, Any]:
        """
        Executes a command in the sandbox and returns legacy-format dict.
        """
        try:
            result = sandbox_manager.execute_command(str(user_id), command, cwd)
            output = result.get("data", {}).get("output", "")
            exit_code = result.get("data", {}).get("exit_code", 0)
            return {"stdout": output, "stderr": "", "exit_code": exit_code}
        except Exception as e:
            logger.error(f"LegacySandboxAdapter.execute_command error: {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": -1}


# Global instance — same interface as the old sandbox_manager
# but now backed by the real sandbox API
legacy_sandbox = LegacySandboxAdapter()

# Keep old name working for any code that does:
#   from core.sandbox import sandbox_manager
# (points to the real SandboxManager, not the legacy adapter)
__all__ = ["sandbox_manager", "legacy_sandbox", "SandboxManager", "SandboxMode", "SandboxClient", "SandboxInfo"]

