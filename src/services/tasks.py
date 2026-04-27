"""Task scheduler for proactive reminders."""
import fcntl
import json
import logging
import time
from typing import Optional

from src.core.config import config

logger = logging.getLogger("vika.tasks")


class TaskScheduler:
    """Persistent task/reminder manager."""

    def __init__(self):
        self._tasks: list[dict] = self._load()

    def _load(self) -> list[dict]:
        try:
            with open(config.tasks_file, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.warning(f"Tasks load error: {e}")
            return []

    def _save(self):
        try:
            with open(config.tasks_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(self._tasks, f, indent=4, ensure_ascii=False)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logger.error(f"Tasks save error: {e}")

    def add(self, message: str, trigger_time: float) -> dict:
        task = {"message": message, "time": trigger_time, "done": False}
        self._tasks.append(task)
        self._save()
        logger.info(f"Task added: {message[:50]} at {trigger_time}")
        return task

    def due(self) -> list[dict]:
        """Return and mark done tasks that are due."""
        now = time.time()
        due_tasks = []
        remaining = []
        for task in self._tasks:
            if task.get("time", 0) <= now and not task.get("done", False):
                task["done"] = True
                due_tasks.append(task)
            else:
                remaining.append(task)
        self._tasks = remaining
        self._save()
        return due_tasks

    def list_pending(self) -> list[dict]:
        return [t for t in self._tasks if not t.get("done", False)]
