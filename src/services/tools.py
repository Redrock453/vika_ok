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
            elif action == "opencode":
                task = params[0] if params else "echo hello"
                return self.opencode.run(task)
            elif action == "opencode_edit":
                path = params[0] if params else "/tmp/test.py"
                changes = params[1] if len(params) > 1 else ""
                return self.opencode.edit_file(path, changes)
            elif action == "opencode_create":
                name = params[0] if params else "project"
                desc = params[1] if len(params) > 1 else ""
                return self.opencode.create_project(name, desc)
            elif action == "opencode_fix":
                path = params[0] if params else "/tmp/test.py"
                bug = params[1] if len(params) > 1 else ""
                return self.opencode.fix_bug(path, bug)
            else:
                return f"❌ Unknown tool: {action}"
        except Exception as e:
            return f"❌ Tool error: {e}"


def build_tool_prompt() -> str:
    """System prompt addition that teaches the LLM to use tools."""
    return """
## Інструменти (TOOLS)

Ти маєш доступ до серверів та інструментів. Замість того щоб пояснювати що треба зробити — РОБИ це!

### SSH інструменти
Формат виклику (пиши прямо в відповіді):
[TOOL:ssh_run:SERVER:COMMAND] — виконати команду на сервері
[TOOL:ssh_status:SERVER] — системна інформація
[TOOL:ssh_ls:SERVER:PATH] — список файлів
[TOOL:ssh_cat:SERVER:PATH] — прочитати файл
[TOOL:ssh_docker:SERVER] — статус Docker

### OpenCode — делегування задач по коду
[TOOL:opencode:TASK_DESCRIPTION] — виконати задачу через OpenCode AI
[TOOL:opencode_edit:FILE_PATH:CHANGES] — редагувати файл
[TOOL:opencode_create:NAME:DESCRIPTION] — створити новий проєкт
[TOOL:opencode_fix:FILE_PATH:BUG_DESCRIPTION] — виправити баг

OpenCode — це AI-агент який пише код, створює файли, редагує проєкти.
Використовуй його для:
- Написання нового коду
- Рефакторингу
- Виправлення багів
- Створення проєктів з нуля
- Аналізу коду

Доступні сервери:
- sitl (100.123.130.38) — ArduPilot SITL
- vika-do-v2 (100.68.33.14) — основний сервер

ПРАВИЛА:
1. Коли Бас просить щось перевірити/зробити на сервері — ВИКОНУЙ команди через [TOOL:ssh_...]
2. Коли Бас просить написати/виправити код — делегуй через [TOOL:opencode:...]
3. НЕ пояснюй які команди треба виконати — ВИКОНУЙ їх!
4. Після виконання — проаналізуй результат і дай коротку відповідь
5. Можеш виконувати кілька команд послідовно
"""
