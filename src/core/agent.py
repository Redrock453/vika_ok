"""Vika_Ok — main agent with RAG, history, tools, and LLM fallback chain."""
import logging

from src.core.config import config
from src.core.history import HistoryManager
from src.core.llm import LLMProvider
from src.services.rag import RAGService
from src.services.search import web_search
from src.services.tools import ToolExecutor, build_tool_prompt

logger = logging.getLogger("vika.agent")

SYSTEM_PROMPT = (
    "Ти — Vika_Ok v13.0. Дружина та інженер Вячеслава (позивний БАС). "
    "Квітень 2026. Відповідай українською, коротко і по суті. "
    "Май контекст розмови. Будь корисною.\n\n"
    + build_tool_prompt()
)


class VikaOk:
    """Core AI agent with RAG + LLM fallback + tools."""

    def __init__(self):
        self.llm = LLMProvider()
        self.history = HistoryManager()
        self.rag = RAGService()
        self.tools = ToolExecutor()
        self.ssh = self.tools.ssh  # backward compat

    def ask(self, query: str, user_id: str = "default") -> str:
        """Process a user query and return response."""
        # Build messages
        rag_context = self.rag.search(query)
        recent = self.history.recent(user_id)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if rag_context:
            messages.append({"role": "system", "content": f"Контекст з бази знань:\n{rag_context}"})
        messages.extend(recent)
        messages.append({"role": "user", "content": query})

        # Get initial response from LLM
        response = self.llm.ask(messages)

        # Check for tool calls and execute them
        tool_results = self.tools.parse_and_execute(response)
        if tool_results:
            # If tools were called, feed results back to LLM for final answer
            tool_output = "\n\n".join(
                f"Команда: {r['call']}\nРезультат:\n{r['result']}"
                for r in tool_results
            )
            messages.append({"role": "assistant", "content": response})
            messages.append({
                "role": "user",
                "content": f"Ось результати виконання команд:\n\n{tool_output}\n\n"
                           f"Проаналізуй результати і дай коротку відповідь Басу українською.",
            })
            response = self.llm.ask(messages)

        # Save to history (only user query and final response)
        self.history.add(user_id, "user", query)
        self.history.add(user_id, "assistant", response)

        return response

    def research(self, topic: str) -> str:
        """Deep research: web search + LLM analysis."""
        search_results = web_search(topic)
        prompt = f"Проаналізуй дані та склади звіт по темі: {topic}\n\nДані:\n{search_results}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return self.llm.ask(messages)

    def transcribe(self, file_path: str) -> str | None:
        """Transcribe audio file to text."""
        return self.llm.transcribe_audio(file_path)

    def new_chat(self, user_id: str):
        """Reset conversation history for user."""
        self.history.clear(user_id)
