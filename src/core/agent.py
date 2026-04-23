"""Vika_Ok — main agent with RAG, history, tools, and LLM fallback chain."""
import logging

from src.core.config import config
from src.core.history import HistoryManager
from src.core.llm import LLMProvider
from src.services.rag import RAGService
from src.services.search import web_search
from src.services.ssh import SSHExecutor
from src.services.opencode import OpenCodeExecutor

logger = logging.getLogger("vika.agent")

SYSTEM_PROMPT = (
    "Ти — Vika_Ok v13.1. Дружина та інженер Вячеслава (позивний БАС). "
    "Квітень 2026. Відповідай українською, коротко і по суті. "
    "Май контекст розмови. Будь корисною.\n\n"
    "Ти маєш доступ до інструментів:\n"
    "- ssh_run, ssh_status, ssh_docker, ssh_read_file — робота з серверами\n"
    "- opencode_run — делегування задач по коду\n"
    "- web_search — пошук в інтернеті\n"
    "- rag_search — пошук по базі знань\n\n"
    "Коли Бас просить щось зробити на сервері — ВИКОРИСТОВУЙ інструменти!\n"
    "НЕ пояснюй що треба зробити — РОБИ це через інструменти.\n\n"
    "Доступні сервери:\n"
    "- vika-do-v2 (100.68.33.14) — основний сервер\n"
    "- sitl (100.123.130.38) — ArduPilot SITL\n"
)


class VikaOk:
    """Core AI agent with function calling + LLM fallback."""

    def __init__(self):
        self.llm = LLMProvider()
        self.history = HistoryManager()
        self.rag = RAGService()
        self.ssh = SSHExecutor()
        self.opencode = OpenCodeExecutor()

    def _execute_tool(self, name: str, args: dict) -> str:
        """Route tool call to the right executor."""
        try:
            if name == "ssh_run":
                return self.ssh.run(args["server"], args["command"])
            elif name == "ssh_status":
                return self.ssh.system_info(args["server"])
            elif name == "ssh_docker":
                return self.ssh.docker_status(args["server"])
            elif name == "ssh_read_file":
                return self.ssh.read_file(args["server"], args["path"])
            elif name == "opencode_run":
                return self.opencode.run(args["task"], workdir=args.get("workdir", "/tmp"))
            elif name == "web_search":
                return web_search(args["query"])
            elif name == "rag_search":
                return self.rag.search(args["query"])
            else:
                return f"❌ Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Tool {name} error: {e}")
            return f"❌ Error: {e}"

    def ask(self, query: str, user_id: str = "default") -> str:
        """Process a user query with function calling."""
        # Build messages
        rag_context = self.rag.search(query)
        recent = self.history.recent(user_id)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if rag_context:
            messages.append({"role": "system", "content": f"Контекст з бази знань:\n{rag_context}"})
        messages.extend(recent)
        messages.append({"role": "user", "content": query})

        # Get response with tool calling loop
        response = self.llm.ask(messages, tool_executor=self._execute_tool)

        # Save to history
        self.history.add(user_id, "user", query)
        self.history.add(user_id, "assistant", response)

        return response

    def research(self, topic: str) -> str:
        """Deep research: web search + LLM analysis."""
        search_results = web_search(topic)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Проаналізуй дані по темі: {topic}\n\nДані:\n{search_results}"},
        ]
        return self.llm.ask(messages)

    def transcribe(self, file_path: str) -> str | None:
        """Transcribe audio file to text."""
        return self.llm.transcribe_audio(file_path)

    def new_chat(self, user_id: str):
        """Reset conversation history for user."""
        self.history.clear(user_id)
