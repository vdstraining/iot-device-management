from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional


DEFAULT_COMMANDS_PATH = str(Path(__file__).parent / "default_commands.json")


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log_message(message: str, logger: Optional[Any] = None) -> None:
    formatted = f"[{_now_ts()}] {message}\n"
    if logger and hasattr(logger, "log"):
        try:
            logger.log(formatted)
            return
        except Exception:
            pass
    print(formatted, end="")


def load_default_commands(path: str, logger: Optional[Any] = None) -> List[dict]:
    """Load default commands from a JSON file.

    Returns a list of dictionaries with keys ``name`` and ``payload``.
    If the file is missing, malformed, or has an invalid schema, returns an empty list.
    """
    p = Path(path)
    if not p.exists():
        _log_message(f"Default commands file not found: {path}", logger)
        return []

    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        _log_message(f"Error reading/parsing default commands: {exc}", logger)
        return []

    if not isinstance(data, list):
        _log_message("Invalid default commands format: root must be a list", logger)
        return []

    valid: List[dict] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            _log_message(f"Skipping invalid command at index {idx}: not an object", logger)
            continue
        name = item.get("name")
        payload = item.get("payload")
        if not isinstance(name, str) or payload is None:
            _log_message(
                f"Skipping invalid command at index {idx}: missing or invalid name/payload",
                logger,
            )
            continue
        valid.append({"name": name, "payload": payload})

    return valid


def save_default_commands(path: str, commands: List[dict], logger: Optional[Any] = None) -> None:
    """Persist default command definitions to a JSON file."""
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(commands, indent=2, ensure_ascii=False), encoding="utf-8")
        _log_message(f"Saved default commands to: {path}", logger)
    except Exception as exc:
        _log_message(f"Error saving default commands: {exc}", logger)


DEFAULT_COMMANDS = load_default_commands(DEFAULT_COMMANDS_PATH)


class AppLogger:
    def __init__(self, callback) -> None:
        self.callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.callback(f"[{timestamp}] {message}\n")
