import json
from pathlib import Path
from typing import Dict, List


class SessionManager:
    def __init__(self, storage_path: str = "session_history.json") -> None:
        self.storage_path = Path(storage_path)
        self.history: List[Dict[str, str]] = self._load()

    def _load(self) -> List[Dict[str, str]]:
        if not self.storage_path.exists():
            return []
        return json.loads(self.storage_path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.storage_path.write_text(json.dumps(self.history, indent=2), encoding="utf-8")

    def append_turn(self, role: str, text: str) -> None:
        self.history.append({"role": role, "text": text})
        self.save()

    def clear(self) -> None:
        self.history = []
        self.save()
