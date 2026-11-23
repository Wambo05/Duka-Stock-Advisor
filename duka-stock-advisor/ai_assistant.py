import os
from typing import Dict, List
import requests

from prompts import SYSTEM_INSTRUCTION, build_inventory_prompt


class AIAssistant:
    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")
        self.api_key = api_key
        raw_model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.model = raw_model.removeprefix("models/")
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

    def ask(
        self,
        user_message: str,
        inventory_context: str,
        past_history: List[Dict[str, str]],
    ) -> str:
        contents: List[dict] = []

        for turn in past_history:
            role = "user" if turn["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": turn["text"]}],
            })

        prompt_with_context = build_inventory_prompt(user_message, inventory_context)
        contents.append({
            "role": "user",
            "parts": [{"text": prompt_with_context}],
        })

        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
            },
        }

        response = requests.post(
            self.endpoint,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "No response generated."
        parts = candidates[0].get("content", {}).get("parts", [])
        texts = [p.get("text", "") for p in parts if "text" in p]
        return "\n".join(texts).strip() or "No response generated."
