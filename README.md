# DUKA Stock Advisor

**GitHub repository:** [wca-ai-tool-s12-PyNova
](https://github.com/Wambo05/wca-ai-tool-s12-PyNova
)

## Group members

1. Jeremiah Eli Ngwono Chuchu
2. Wangui Lucy Wambui
3. Fredrick Maina

## Project overview

DUKA Stock Advisor is a Python command-line assistant for small shops. A shopkeeper can describe stock changes and ask questions in everyday language. Gemini interprets each message and returns structured JSON; the Python program validates the response and performs the actual stock calculations.

The app keeps conversation context during a session, tracks inventory and transactions between runs, and creates a saved summary when a session ends.

## Features

- Add products and record incoming stock.
- Record sales and update remaining quantities.
- Check a product's stock and reorder level.
- List products at or below their reorder levels.
- Review transaction history and sales summaries.
- Keep conversation history during a session.
- Validate Gemini's JSON response and retry once if it is invalid.
- Generate and save a session summary as a dated JSON file.
- Open and display a previous saved session from the menu.

## Project files

| File or folder | Purpose |
| --- | --- |
| `main.py` | Starts the application and displays the main menu. |
| `ai_assistant.py` | Connects to Gemini, manages conversation history, validates AI responses, and runs a shopkeeper session. |
| `prompts.py` | Contains the conversation and session-summary instructions sent to Gemini. |
| `inventory.py` | Performs stock operations, calculations, and transaction lookups. |
| `inventory.json` | Stores current inventory quantities and reorder levels. |
| `activity_log.json` | Stores successful stock and sales transactions. |
| `session_manager.py` | Saves sessions, opens previous sessions, and formats summaries. |
| `sessions/` | Stores dated session transcripts and summaries. |
| `samples/` | Contains a sample session for the project submission. |
| `test_gemini.py` | Checks whether the Gemini API connection is working. |
| `requirements.txt` | Lists the Python packages required by the project. |
| `.env` | Stores the Gemini API key locally and is excluded from Git. |

## Requirements

- Python 3
- A Gemini API key
- Internet access when making Gemini requests

## Setup

Open PowerShell in the project folder and create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a file named `.env` in the project folder and add your Gemini API key:

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

Keep the real key private. The `.gitignore` file excludes `.env` from Git. You can also set the key for the current PowerShell session instead of using `.env`:

```powershell
$env:GEMINI_API_KEY = "your_gemini_api_key_here"
```

## Run the application

With the virtual environment active, run:

```powershell
python main.py
```

The menu offers these options:

1. **Start a new session** — enter stock requests and questions. Type `exit` to finish; the app generates a summary and saves the session.
2. **Open a previous session** — choose a saved session to display its conversation and summary.
3. **Exit** — close the application.

To check the Gemini API connection separately, run:

```powershell
python test_gemini.py
```

## Data and privacy

Inventory and transaction data are stored in local JSON files. Session transcripts and summaries are stored in `sessions/`. Do not add API keys or private customer information to sample files or the GitHub repository. Review generated session files before sharing them.

## Sample session

The project sample is `samples/sample_session_2026-11-23.json`. It demonstrates a multi-turn session, a sale, a stock check, a low-stock alert, and the final summary.

