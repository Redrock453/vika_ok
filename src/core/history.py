"""Chat history management with persistence."""
import json
import logging
import threading
from typing import Optional, List, Dict

from src.core.config import config

logger = logging.getLogger("vika.history")

# File locking (Unix only, no-op on Windows)
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


class HistoryManager:
    """Thread-safe chat history with JSON persistence and file locking."""

    def __init__(self):
        self._histories: Dict[str, List[Dict[str, str]]] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        try:
            with open(config.history_file, "r") as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for read
                try:
                    self._histories = json.load(f)
                    logger.info(f"Loaded history for {len(self._histories)} users")
                finally:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except FileNotFoundError:
            logger.info("History file not found, starting fresh")
            self._histories = {}
        except Exception as e:
            logger.warning(f"History load error: {e}")
            self._histories = {}

    def _save(self):
        """Save histories with file locking."""
        try:
            with open(config.history_file, "w") as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock for write
                try:
                    json.dump(self._histories, f, ensure_ascii=False, indent=2)
                finally:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"History save error: {e}")

    def get(self, user_id: str) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._histories.get(str(user_id), []))

    def add(self, user_id: str, role: str, content: str):
        """Add message to user history with automatic cleanup."""
        with self._lock:
            uid = str(user_id)
            if uid not in self._histories:
                self._histories[uid] = []
            self._histories[uid].append({"role": role, "content": content})
            # Trim to 2x max to allow some buffer
            if len(self._histories[uid]) > config.max_history_storage:
                self._histories[uid] = self._histories[uid][-config.max_history:]
            self._save()

    def clear(self, user_id: str) -> bool:
        """Clear history for user. Return True if cleared."""
        with self._lock:
            uid = str(user_id)
            if uid in self._histories:
                del self._histories[uid]
                self._save()
                return True
            return False

    def recent(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        limit = limit or config.max_history
        return self.get(user_id)[-limit:]

    def get_all_user_ids(self) -> List[str]:
        """Get all user IDs with history."""
        with self._lock:
            return list(self._histories.keys())
