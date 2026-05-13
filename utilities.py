import json
from datetime import datetime


with open("default_commands.json", "r") as f:
    DEFAULT_COMMANDS = json.load(f)


class AppLogger:
    def __init__(self, callback) -> None:
        self.callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.callback(f"[{timestamp}] {message}\n")
