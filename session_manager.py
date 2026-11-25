import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

SUMMARY_FAILED_MESSAGE = (
    "AI summary could not be generated. The conversation has still been saved."
)


def format_summary(summary):
    """Turn a summary dict into readable text (also handles old string summaries)."""

    if not summary:
        return SUMMARY_FAILED_MESSAGE

    if isinstance(summary, str):
        return summary

    lines = [summary.get("overview", "")]
    sections = [
        ("Products discussed", "products_discussed"),
        ("Stock changes", "stock_changes"),
        ("Low-stock alerts", "low_stock_alerts"),
        ("Recommendations", "recommendations"),
        ("Notes", "notes"),
    ]

    for title, key in sections:
        items = summary.get(key, [])
        if items:
            lines.append(f"\n{title}:")
            for item in items:
                if isinstance(item, dict):
                    item = ", ".join(f"{name}: {value}" for name, value in item.items())
                lines.append(f"  - {item}")

    return "\n".join(lines)


def save_session(summary, session_activity, model):
    """Save a conversation and summary to a dated JSON file."""

    if not session_activity:
        print("\nNo conversation to save.")
        return None

    timestamp = datetime.now()
    filename = f"session_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    file_path = SESSIONS_DIR / filename
    session_data = {
        "session_date": timestamp.isoformat(timespec="seconds"),
        "model": model,
        "conversation": session_activity,
        "summary": summary,
    }

    try:
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(session_data, file, indent=4, ensure_ascii=False)
        temp_path.replace(file_path)
        print(f"\nSession successfully saved: {file_path}")
        return file_path
    except (OSError, TypeError, ValueError) as error:
        print(f"\nCould not save session: {error}")
        return None


def open_previous_session():
    """List saved sessions and display the one the user selects."""

    session_files = sorted(
        SESSIONS_DIR.glob("session_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not session_files:
        print("\nNo previous sessions were found.")
        return

    print("\nPREVIOUS SESSIONS")
    for index, path in enumerate(session_files, start=1):
        print(f"{index}. {path.name}")
    print("0. Return to main menu")

    choice = input("\nSelect a session: ").strip()
    if choice == "0":
        return

    try:
        selected_index = int(choice) - 1
        if selected_index < 0 or selected_index >= len(session_files):
            print("Invalid session selection.")
            return

        with open(session_files[selected_index], "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Session file must contain a JSON object.")

        print("\n========== SAVED SESSION ==========")
        print(f"Date: {data.get('session_date', 'Unknown')}")
        print("\nCONVERSATION:")
        conversation = data.get("conversation", [])
        if not isinstance(conversation, list):
            raise ValueError("Session conversation must be a list.")

        for turn in conversation:
            if not isinstance(turn, dict):
                continue
            print(f"\nShopkeeper: {turn.get('user_message', '')}")
            print(f"AI Assistant: {turn.get('ai_reply', '')}")

        print("\nFINAL SESSION SUMMARY:")
        print(format_summary(data.get("summary")))
        print("\n===================================")

    except ValueError:
        print("Please enter a valid session number or choose a valid session file.")
    except (OSError, json.JSONDecodeError, TypeError) as error:
        print(f"Could not open session: {error}")
