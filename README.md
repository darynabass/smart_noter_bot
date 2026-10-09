# Smart Noter Bot

Smart Noter Bot is a Telegram bot for managing personal notes, reminders, and custom lists. It also provides activity statistics and sends scheduled reminders in the background.

## Features

* Create and manage notes
* Create reminders and choose their priority
* Create and view custom lists
* Edit item text, priority, and reminder schedule
* Mark reminders as completed
* View user activity statistics
* Send scheduled reminders in the background

## Tech Stack

* **Python 3.10+**
* **aiogram 3.x** — asynchronous framework for the Telegram Bot API
* **aiosqlite** — asynchronous interface for SQLite
* **python-dotenv** — loads environment variables from a `.env` file
* **SQLite** — database

## Requirements

Before running the bot, make sure you have:

* Python 3.10 or newer
* A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Installation and Setup

### 1\. Clone or download the project

Open a terminal in the project directory.

### 2\. Create a virtual environment

```bash
python -m venv .venv
```

### 3\. Activate the virtual environment

**Windows — PowerShell**

```powershell
.\\.venv\\Scripts\\Activate.ps1
```

**Windows — Command Prompt**

```bat
.venv\\Scripts\\activate.bat
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 4\. Install dependencies

```bash
pip install -r requirements.txt
```

### 5\. Configure the bot token

Create a `.env` file in the project root and add your Telegram bot token:

```env
BOT\_TOKEN=your\_bot\_token\_here
```

Replace `your\_bot\_token\_here` with the token provided by BotFather. Keep your real `.env` file private and do not commit it to a public repository.

### 6\. Run the bot

```bash
python main.py
```

## Quick Start on Windows

You can use the included batch files instead:

1. Run `setup.bat` to prepare the environment.
2. Run `run.bat` to start the bot.

If either script does not work in your environment, follow the manual setup instructions above.

## Project Structure

```text
SMART\_NOTER\_BOT/
├── main.py                  # Application entry point
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── .env                     # Local environment variables (create locally)
├── .gitignore
├── run.bat                  # Windows launch script
├── setup.bat                # Windows setup script
├── database/
│   ├── db.py                # Database connection and setup
│   └── queries.py            # Database queries
├── handlers/                # Telegram command and interaction handlers
│   ├── start.py
│   ├── fallback.py
│   ├── add.py
│   ├── lists.py
│   ├── items.py
│   ├── notes.py
│   ├── reminders.py
│   └── stats.py
├── keyboards/               # Telegram keyboard layouts
│   ├── pagination.py
│   ├── main\_menu.py
│   ├── add\_keyboards.py
│   ├── list\_keyboards.py
│   ├── time\_keyboards.py
│   └── item\_keyboards.py
├── services/
│   └── reminder\_service.py  # Scheduled reminder service
└── utils/                   # Shared utilities and formatting helpers
    ├── text\_utils.py
    ├── constants.py
    ├── priority\_utils.py
    ├── message\_utils.py
    ├── formatters.py
    └── datetime\_utils.py
```

The SQLite database file is created or used by the application according to its database configuration. It is not listed above because the local database is runtime data rather than source code.

## Documentation

The source code uses Doxygen-style documentation comments. If the project includes a `Doxyfile` and Doxygen is installed, generate HTML documentation with:

```bash
doxygen Doxyfile
```

## Author

**Daryna Bass**

Developed as part of a diploma thesis.

