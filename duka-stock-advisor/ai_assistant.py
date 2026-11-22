import json
import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-2.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _call_gemini(prompt: str, temperature: float = 0.2, json_mode: bool = False) -> dict:
    if not API_KEY:
        return {"ok": False, "text": "", "error": "GEMINI_API_KEY is not set."}

    url = f"{BASE_URL}/{DEFAULT_MODEL}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        candidates = body.get("candidates") or []
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            return {"ok": False, "text": "", "error": "Empty response from Gemini."}
        return {"ok": True, "text": text, "error": None}
    except Exception as exc:
        return {"ok": False, "text": "", "error": str(exc)}


def extract_intent(prompt: str, mock: bool = False) -> dict:
    if mock or not API_KEY:
        return {
            "ok": True,
            "action": "check_stock",
            "item": "sample_item",
            "quantity": 1,
            "error": None,
        }

    res = _call_gemini(prompt, temperature=0.0, json_mode=True)
    if not res["ok"]:
        return {
            "ok": False,
            "action": "unknown",
            "item": None,
            "quantity": None,
            "error": res["error"],
        }

    try:
        data = json.loads(res["text"])
        return {
            "ok": True,
            "action": data.get("action", "unknown"),
            "item": data.get("item"),
            "quantity": data.get("quantity"),
            "error": None,
        }
    except json.JSONDecodeError:
        return {
            "ok": False,
            "action": "unknown",
            "item": None,
            "quantity": None,
            "error": "Model returned invalid JSON.",
        }


def generate_response(prompt: str, mock: bool = False) -> dict:
    if mock or not API_KEY:
        return {
            "ok": True,
            "reply": "[MOCK AI REPLY] Inventory data received and processed.",
            "error": None,
        }

    res = _call_gemini(prompt, temperature=0.3, json_mode=False)
    if not res["ok"]:
        return {
            "ok": False,
            "reply": "Sorry, the AI assistant is temporarily unavailable. Please try again.",
            "error": res["error"],
        }

    return {"ok": True, "reply": res["text"], "error": None}


if __name__ == "__main__":
    print("Intent test:", extract_intent("Check stock for sugar", mock=True))
    print("Reply test:", generate_response("We have 12 packets of sugar.", mock=True))
