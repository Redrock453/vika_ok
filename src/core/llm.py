"""LLM provider clients with retry, fallback chain, and function calling."""
import logging
import time
import json
from typing import Optional

from openai import OpenAI

from src.core.config import config
from src.services.tool_defs import TOOLS

logger = logging.getLogger("vika.llm")

MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 5]


class LLMProvider:
    """Manages LLM clients with automatic retry, fallback, and tool calling."""

    def __init__(self):
        self.do_client: Optional[OpenAI] = None
        self.groq_client: Optional[OpenAI] = None
        self.gemini_model = None

        self._init_do()
        self._init_groq()
        self._init_gemini()

        # Fallback chain: DO → Groq → Gemini
        self.chain = [
            ("do", self._call_do),
            ("groq", self._call_groq),
            ("gemini", self._call_gemini),
        ]

    def _init_do(self):
        if not config.do_api_key:
            return
        try:
            self.do_client = OpenAI(
                base_url=config.do_base_url,
                api_key=config.do_api_key,
            )
            logger.info("DO Agent initialized")
        except Exception as e:
            logger.warning(f"DO init failed: {e}")

    def _init_groq(self):
        if not config.groq_api_key:
            return
        try:
            self.groq_client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=config.groq_api_key,
            )
            logger.info("Groq initialized")
        except Exception as e:
            logger.warning(f"Groq init failed: {e}")

    def _init_gemini(self):
        if not config.gemini_api_key:
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-pro")
            logger.info("Gemini initialized")
        except Exception as e:
            logger.warning(f"Gemini init failed: {e}")

    def _call_do(self, messages: list[dict], tools=None) -> dict:
        """Returns dict with 'content' and optional 'tool_calls'."""
        if not self.do_client:
            return None
        kwargs = {"model": "openai-gpt-oss-120b", "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self.do_client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        result = {"content": choice.message.content or ""}
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            result["tool_calls"] = choice.message.tool_calls
        return result

    def _call_groq(self, messages: list[dict], tools=None) -> dict:
        if not self.groq_client:
            return None
        kwargs = {"model": "llama-3.3-70b-versatile", "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self.groq_client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        result = {"content": choice.message.content or ""}
        if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
            result["tool_calls"] = choice.message.tool_calls
        return result

    def _call_gemini(self, messages: list[dict], tools=None) -> dict:
        if not self.gemini_model:
            return None
        # Gemini doesn't support function calling in this wrapper — flatten
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        res = self.gemini_model.generate_content(prompt, request_options={"timeout": 90})
        return {"content": res.text.strip()}

    def ask(self, messages: list[dict], tool_executor=None) -> str:
        """
        Try each provider with retries. If tool_calls returned,
        execute them and loop back to LLM for final answer.
        Max 5 tool call rounds to prevent infinite loops.
        """
        for round_num in range(5):
            result = None
            for name, caller in self.chain:
                for attempt in range(MAX_RETRIES):
                    try:
                        result = caller(messages, tools=TOOLS if tool_executor else None)
                        if result:
                            break
                    except Exception as e:
                        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                        logger.warning(f"[{name}] attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(delay)
                if result:
                    break

            if not result:
                return "❌ Всі провайдери недоступні. Спробуй пізніше."

            # No tool calls — return content
            if "tool_calls" not in result or not result["tool_calls"]:
                return result["content"]

            # Execute tool calls
            if not tool_executor:
                return result["content"]

            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": result["content"] or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in result["tool_calls"]
                ]
            })

            # Execute each tool call and add results
            for tc in result["tool_calls"]:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                logger.info(f"Tool call: {fn_name}({fn_args})")

                tool_result = tool_executor(fn_name, fn_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(tool_result),
                })

            # Loop back to LLM with tool results

        return "⚠️ Досягнуто ліміт викликів інструментів."

    def transcribe_audio(self, file_path: str) -> Optional[str]:
        """Transcribe audio via Groq Whisper."""
        if not self.groq_client:
            return None
        with open(file_path, "rb") as f:
            result = self.groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                response_format="text",
            )
        return result.text.strip() if hasattr(result, "text") else str(result)
