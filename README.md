# Gmail Summariser & Reply Agent ✉️🧠

LangChain REACT agent that plugs into the **Claude‑Post** email MCP server.
* 🔍 *Search & summarise* Gmail threads
* ✉️ *Draft & reply* — **asks for confirmation first**

## Quick‑start (Windows‑friendly)

```powershell
# 0. Prereqs: Python 3.10+, Node (for the email MCP server), Git
# 1. Unzip / cd into the folder
cd email_agent_project

# 2. Create & activate virtual‑env
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install deps (pulls claude‑post straight from GitHub)
pip install -r requirements.txt

# 4. Configure credentials
copy .env.example .env
notepad .env   # paste your OpenAI + Gmail app password
```

Run the agent:

```powershell
python email_agent.py
```

Example dialog:

```
> Summarise unread emails from the last 2 days
(assistant prints a concise summary)

> Reply to the latest email from Sarah confirming the meeting.
(assistant drafts the email, shows the full text, and asks "Send this email? (yes/no)")
```

## How it works

| Layer | Function |
| ----- | -------- |
| **Claude‑Post MCP server** | Provides structured tools: search, read, send |
| **langchain-mcp-adapters** | Launches `email-client` and wraps its tools |
| **LangChain REACT agent** | Chooses tools based on conversation |
| **System Prompt** | Enforces confirmation before sending |

## Security tips

* Use a **Gmail App Password** (2FA required) instead of your main password.
* `.env` is in `.gitignore` – keep it out of source control.
* The agent never sends without an explicit “yes”.

Enjoy inbox‑taming bliss!