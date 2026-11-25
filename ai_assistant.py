import os
import json
import math
import time
from datetime import datetime
from copy import deepcopy

from google import genai
from google.genai import types
from dotenv import load_dotenv

import inventory as inventory_module
from prompts import SYSTEM_PROMPT, SUMMARY_PROMPT
from session_manager import format_summary, save_session

# =========================================================
# 1. CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Check your .env file.")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-3.5-flash-lite"

# Conversation and activity records for the current session
conversation_history = []
session_activity = []

VALID_ACTIONS = {
    "add_product",
    "record_sale",
    "receive_stock",
    "set_reorder_level",
    "check_stock",
    "list_low_stock",
    "get_activity_history",
    "get_sales_summary",
}


# =========================================================
# 2. GEMINI ERROR HANDLING AND RETRIES
# =========================================================


def is_retryable_error(error):
    """Identify temporary API errors that may succeed on retry."""

    message = str(error).lower()

    retryable_codes = ("503", "429", "500", "502", "504")

    return (
        any(code in message for code in retryable_codes)
        or "unavailable" in message
        or "resource exhausted" in message
        or "too many requests" in message
    )


def generate_with_retry(model, contents, config):
    """Retry temporary Gemini errors using exponential backoff."""

    delays = [2, 4, 8]

    for attempt in range(len(delays) + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

        except Exception as error:

            if not is_retryable_error(error):
                raise

            if attempt == len(delays):
                raise

            wait_time = delays[attempt]

            print(
                f"\nGemini is temporarily unavailable. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


# =========================================================
# 3. VALIDATE GEMINI JSON RESPONSES
# =========================================================


def validate_ai_response(response_text):
    """Return the parsed response dict if valid, otherwise None."""

    try:
        data = json.loads(response_text)

        if not isinstance(data, dict):
            return None

        if not isinstance(data.get("reply"), str):
            return None

        if not data["reply"].strip():
            return None

        if not isinstance(data.get("actions"), list):
            return None

        for action in data["actions"]:

            if not isinstance(action, dict):
                return None

            action_type = action.get("action")

            if action_type not in VALID_ACTIONS:
                return None

            # Sales summary validation
            if action_type == "get_sales_summary":
                continue

            # Transaction history validation
            if action_type == "get_activity_history":

                product = action.get("product", "")
                limit = action.get("limit", 10)
                filter_action = action.get("filter_action")

                if not isinstance(product, str):
                    return None

                if (
                    isinstance(limit, bool)
                    or not isinstance(limit, int)
                    or limit < 1
                    or limit > 100
                ):
                    return None

                if filter_action is not None:
                    if filter_action not in (
                        "sale",
                        "stock_received",
                        "new_product",
                    ):
                        return None

                if "quantity" in action and action["quantity"] != 0:
                    return None

                if "unit" in action and not isinstance(action["unit"], str):
                    return None

                continue

            # Standard inventory action validation
            product = action.get("product")
            quantity = action.get("quantity")
            unit = action.get("unit")

            if not isinstance(product, str):
                return None

            if not isinstance(unit, str):
                return None

            if (
                isinstance(quantity, bool)
                or not isinstance(quantity, (int, float))
                or not math.isfinite(quantity)
            ):
                return None

            if action_type == "list_low_stock":

                if quantity != 0 or product != "":
                    return None

            elif action_type == "check_stock":

                if quantity != 0 or not product.strip():
                    return None

            else:

                if quantity <= 0 or not product.strip():
                    return None

            if action_type == "add_product" and not unit.strip():
                return None

        return data

    except (json.JSONDecodeError, TypeError, ValueError):
        return None


# =========================================================
# 4. GET GEMINI RESPONSE WITH CONVERSATION MEMORY
# =========================================================


def get_gemini_response(user_message, inventory_snapshot):
    """Send the full history plus verified data to Gemini (retries once)."""

    inventory_context = json.dumps(
        inventory_snapshot,
        indent=2,
    )

    activity_snapshot = inventory_module.get_activity_history(limit=100)

    activity_context = json.dumps(
        activity_snapshot,
        indent=2,
    )

    user_content = (
        f"CURRENT INVENTORY:\n{inventory_context}\n\n"
        f"TRANSACTION HISTORY:\n{activity_context}\n\n"
        f"SHOPKEEPER MESSAGE:\n{user_message}"
    )

    # Full history + the new message (history always ends with a model turn)
    contents = conversation_history + [
        types.Content(
            role="user",
            parts=[types.Part(text=user_content)],
        )
    ]

    for attempt in range(2):

        response = generate_with_retry(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )

        result = validate_ai_response(response.text or "")

        if result is not None:

            conversation_history.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_content)],
                )
            )

            conversation_history.append(
                types.Content(
                    role="model",
                    parts=[types.Part(text=json.dumps(result))],
                )
            )

            return result

        if attempt == 0:

            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=(
                                "Your previous response was invalid. "
                                "Return valid JSON using the required format."
                            )
                        )
                    ],
                )
            )

    raise ValueError("Gemini returned invalid JSON after one retry.")


# =========================================================
# 5. PROCESS SHOPKEEPER MESSAGES
# =========================================================


def process_shopkeeper_message(user_message):
    """Get the AI's actions, let Python execute them, and build the reply."""

    if not isinstance(user_message, str) or not user_message.strip():
        raise ValueError("Please enter a message.")

    inventory_snapshot = deepcopy(inventory_module.inventory)

    result = get_gemini_response(
        user_message,
        inventory_snapshot,
    )

    # Python performs the real stock updates and calculations
    action_results = inventory_module.execute_actions(result["actions"])

    final_reply = result["reply"]

    if action_results:
        final_reply += "\n\nInventory results:\n"
        final_reply += "\n".join(action_results)

    result["reply"] = final_reply
    result["action_results"] = action_results

    activity_record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_message": user_message,
        "ai_reply": final_reply,
        "actions": result["actions"],
        "action_results": action_results,
        "inventory_after": deepcopy(inventory_module.inventory),
    }

    session_activity.append(activity_record)

    # Keep the final displayed response in conversation memory.
    conversation_history[-1] = types.Content(
        role="model",
        parts=[types.Part(text=json.dumps(result))],
    )

    return result


# =========================================================
# 6. GENERATE FINAL SESSION SUMMARY
# =========================================================

# Fields the summary JSON must contain, and the type of each
SUMMARY_FIELDS = {
    "overview": str,
    "products_discussed": list,
    "stock_changes": list,
    "low_stock_alerts": list,
    "recommendations": list,
    "notes": list,
}

SUMMARY_FAILED_MESSAGE = (
    "AI summary could not be generated. The conversation has still been saved."
)


def validate_summary(response_text):
    """Return the summary dict if valid, otherwise None."""

    try:
        data = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        return None

    if not isinstance(data, dict):
        return None

    for field, expected_type in SUMMARY_FIELDS.items():
        if not isinstance(data.get(field), expected_type):
            return None

    return data


def generate_session_summary():
    """Ask Gemini for a JSON summary. Returns a dict, or None on failure."""

    if not session_activity:
        return None

    print("\nGenerating your session summary...")
    transcript = "\n".join(
        f"SHOPKEEPER: {turn['user_message']}\nASSISTANT: {turn['ai_reply']}"
        for turn in session_activity
    )

    activity_log = [
        {
            "time": turn["timestamp"],
            "actions": turn["actions"],
            "results": turn["action_results"],
        }
        for turn in session_activity
    ]

    # ONE user message, so the request ends with a user turn
    request_text = (
        f"CONVERSATION:\n{transcript}\n\n"
        f"SESSION ACTIVITY LOG:\n{json.dumps(activity_log, indent=2)}\n\n"
        f"FINAL INVENTORY:\n{json.dumps(inventory_module.inventory, indent=2)}\n\n"
        "Write the end-of-session summary now, as the JSON object described."
    )

    contents = [types.Content(role="user", parts=[types.Part(text=request_text)])]

    try:
        for _ in range(2):  # first attempt + one retry
            response = generate_with_retry(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SUMMARY_PROMPT,
                    response_mime_type="application/json",
                ),
            )

            summary = validate_summary(response.text or "")
            if summary is not None:
                return summary

            print("Summary response was invalid. Trying once more...")

    except Exception as error:
        print(f"Could not generate AI summary: {error}")

    return None


# =========================================================
# 9. RESET THE CURRENT CONVERSATION
# =========================================================


def reset_conversation():
    """Clear memory so each new session starts fresh."""

    conversation_history.clear()
    session_activity.clear()


# =========================================================
# 10. RUN A NEW SHOPKEEPER SESSION
# =========================================================


def run_new_session():
    """Chat loop for one session; summarizes and saves when it ends."""

    reset_conversation()

    print("\nNew DUKA Stock Advisor session started!")
    print("Type 'exit' to end this session.")

    while True:

        try:
            user_message = input("\nShopkeeper: ")

        except (EOFError, KeyboardInterrupt):
            print("\nSession interrupted.")
            break

        if user_message.strip().lower() == "exit":
            break

        if not user_message.strip():
            print("Please enter a message.")
            continue

        try:

            result = process_shopkeeper_message(user_message)

            print("\nAI Assistant:")
            print(result["reply"])

        except Exception as error:
            print(f"\nError: {error}")
    if session_activity:

        summary = generate_session_summary()

        print("\nFINAL SESSION SUMMARY:")
        print(format_summary(summary))

        # Save the dict if we have one, otherwise a clear fallback message
        save_session(
            summary if summary else SUMMARY_FAILED_MESSAGE,
            session_activity,
            MODEL,
        )

    print("\nSession closed.")
