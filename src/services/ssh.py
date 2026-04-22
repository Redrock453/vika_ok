"""Remote server execution via SSH."""
import logging
import subprocess
from typing import Optional

from src.core.config import config

logger = logging.getLogger("vika.ssh")

# Known servers
SERVERS = {
    "vika-do-v2": "100.68.33.14",
    "sitl": "100.123.130.38",
}


class SSHExecutor:
    """Execute commands on remote servers via SSH."""

    def __init__(self):
        self.key_path = "/root/.ssh/id_ed25519"

    def run(self, host: str, command: str, timeout: int = 30) -> str:
        """Run a command on remote server and return output."""
        # Resolve server name to IP
        target = SERVERS.get(host, host)

        cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", f"ServerAliveInterval={timeout}",
            "-i", self.key_path,
            f"root@{target}",
            command,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout.strip()
            if result.stderr and result.returncode != 0:
                output += f"\n⚠️ {result.stderr.strip()}"
            return output or "(no output)"
        except subprocess.TimeoutExpired:
            return "❌ Timeout"
        except Exception as e:
            return f"❌ SSH error: {e}"

    def list_files(self, host: str, path: str = "/root") -> str:
        """List files on remote server."""
        return self.run(host, f"ls -la {path}")

    def read_file(self, host: str, path: str) -> str:
        """Read file contents from remote server."""
        return self.run(host, f"cat {path}")

    def docker_status(self, host: str) -> str:
        """Check Docker containers on remote server."""
        return self.run(host, "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")

    def system_info(self, host: str) -> str:
        """Get system info from remote server."""
        return self.run(host, "uname -a && echo '---' && free -h | head -2 && echo '---' && df -h / | tail -1")
