"""OpenCode integration — delegate coding tasks to OpenCode agent via SSH."""
import logging
from typing import Optional

from src.services.ssh import SSHExecutor

logger = logging.getLogger("vika.opencode")


class OpenCodeExecutor:
    """Execute coding tasks via OpenCode CLI on vika-do-v2."""

    def __init__(self):
        self.ssh = SSHExecutor()

    def run(self, task: str, model: str = "opencode/minimax-m2.5-free",
            workdir: str = "/tmp", timeout: int = 120) -> str:
        """Run a coding task via OpenCode on vika-do-v2."""
        safe_task = task.replace("'", "'\"'\"'")
        cmd = f"opencode run --model {model} --cwd {workdir} '{safe_task}'"
        return self.ssh.run("vika-do-v2", cmd, timeout=timeout)

    def edit_file(self, file_path: str, changes: str) -> str:
        """Edit a file using OpenCode."""
        task = f"Edit the file {file_path} with these changes: {changes}"
        workdir = "/".join(file_path.split("/")[:-1]) or "/tmp"
        return self.run(task, workdir=workdir)

    def create_project(self, name: str, description: str,
                       base_path: str = "/root/projects") -> str:
        """Create a new project scaffold."""
        task = f"Create a project called '{name}': {description}. Put it in {base_path}/{name}"
        return self.run(task, workdir=base_path)

    def fix_bug(self, file_path: str, bug_description: str) -> str:
        """Fix a bug in a file."""
        task = f"Fix this bug in {file_path}: {bug_description}"
        workdir = "/".join(file_path.split("/")[:-1]) or "/tmp"
        return self.run(task, workdir=workdir)
