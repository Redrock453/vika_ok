"""Tool executor — allows the LLM to invoke SSH and other tools."""
import json
import logging
import re

from src.services.ssh import SSHExecutor

logger = logging.getLogger("vika.tools")

# Tool call format: [TOOL:action:params]
# e.g. [TOOL:ssh_run:sitl:ls -la /root/]
# e.g. [TOOL:ssh_status:sitl]
TOOL_PATTERN = re.compile(r'\[TOOL:(\w+):([^\]]+)\]')


class ToolExecutor:
    """Parses and executes tool calls from LLM responses."""

    def __init__(self):
        self.ssh = SSHExecutor()

    def parse_and_execute(self, llm_response: str) -> list[dict]:
        """Find tool calls in LLM response, execute them, return results."""
        results = []
        for match in TOOL_PATTERN.finditer(llm_response):
            action = match.group(1)
            params = match.group(2).split(":", 1)
            result = self._execute(action, params)
            results.append({
                "call": match.group(0),
                "result": result,
            })
        return results

    def _execute(self, action: str, params: list[str]) -> str:
        try:
            if action == "ssh_run":
                server = params[0] if params else "vika-do-v2"
                cmd = params[1] if len(params) > 1 else "echo hello"
                return self.ssh.run(server, cmd)
            elif action == "ssh_status":
                server = params[0] if params else "vika-do-v2"
                return self.ssh.system_info(server)
            elif action == "ssh_ls":
                server = params[0] if params else "vika-do-v2"
                path = params[1] if len(params) > 1 else "/root"
                return self.ssh.list_files(server, path)
            elif action == "ssh_cat":
                server = params[0] if params else "vika-do-v2"
                path = params[1] if len(params) > 1 else "/etc/hostname"
                return self.ssh.read_file(server, path)
            elif action == "ssh_docker":
                server = params[0] if params else "vika-do-v2"
                return self.ssh.docker_status(server)
            else:
                return f"❌ Unknown tool: {action}"
        except Exception as e:
            return f"❌ Tool error: {e}"


def build_tool_prompt() -> str:
    """System prompt addition that teaches the LLM to use tools."""
    return """
## Інструменти (TOOLS)

Ти маєш доступ до серверів. Замість того щоб пояснювати що треба зробити — РОБИ це!

Формат виклику інструменту (пиши прямо в відповіді):
[TOOL:ssh_run:SERVER:COMMAND] — виконати команду на сервері
[TOOL:ssh_status:SERVER] — системна інформація
[TOOL:ssh_ls:SERVER:PATH] — список файлів
[TOOL:ssh_cat:SERVER:PATH] — прочитати файл
[TOOL:ssh_docker:SERVER] — статус Docker

Доступні сервери:
- sitl (100.123.130.38) — ArduPilot SITL
- vika-do-v2 (100.68.33.14) — основний сервер

ПРАВИЛА:
1. Коли Бас просить щось перевірити/зробити на сервері — ВИКОНУЙ команди через [TOOL:...]
2. НЕ пояснюй які команди треба виконати — ВИКОНУЙ їх!
3. Після виконання — проаналізуй результат і дай коротку відповідь
4. Можеш виконувати кілька команд послідовно

Приклад:
Бас: "зайди на sitl сервер і подивись що там"
Ти: [TOOL:ssh_run:sitl:uname -a && ls -la /root/ && docker ps -a 2>&1]
"""
