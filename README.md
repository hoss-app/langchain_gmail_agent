# Gmail Assistant – Read 📖, Draft ✉️ & Send (Only when you say so)

A tiny Python CLI that:

* **Searches & summarises** your Gmail threads  
* **Drafts replies** and **sends only after you type “yes”**  
* Stores all Google secrets in **`.env`** – no JSON juggling for users  
* Auto‑opens the Google consent screen on first run, then remembers the token  
* Works on Windows, macOS & Linux (Python 3.9+ & Node.js required)

---

## 1  Install

```powershell
# 0 Prereqs – Python 3.9+ & Node.js (includes npx)
git clone <repo>   # or unzip the folder you downloaded
cd langchain_gmail_agent

python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2  Create `.env`

```env
# ---------- OpenAI ----------
OPENAI_API_KEY=sk-...

# ---------- Google OAuth (Desktop‑App creds) ----------
GOOGLE_CLIENT_ID=1234567890-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_PROJECT_ID=gmail-assistant      # optional
```

**How to get those Google values**

1. Google Cloud Console → APIs & Services → **Library** → enable **Gmail API**.  
2. **Credentials** → Create Credentials → **OAuth client ID** → *Desktop app*.  
3. Download the JSON → copy the **client_id** & **client_secret** into `.env`.  
   (You only do this **once per app**; end‑users never touch Google Cloud.)

---

## 3  First run

```powershell
python gmail_oauth_agent.py
```

* Writes `~/.gmail-mcp/gcp-oauth.keys.json` from your `.env` (one‑off).  
* Detects no `credentials.json` → launches **npx gmail-autoauth-mcp auth** → browser pops.  
* Click **Allow** to grant Gmail access.  
* Refresh token saved → chat prompt appears:

```
Ask me about your Gmail (type 'quit' to exit):

> Summarise my latest email
Assistant: Your most recent email is from Sarah…
```

---

## 4  Replying (with confirmation)

```
> Reply thanking her and attaching the slide deck
Assistant: 
Draft:
--------------------------------------------------
To: sarah@example.com
Subject: Re: Demo tomorrow
Body:
Hi Sarah,

Thanks for confirming the demo. Slides attached.

Cheers,
Hossein
--------------------------------------------------
Send this email? (yes/no)
```

*Type* **yes** to send, **no** to cancel.  
The script keeps the full conversation in memory, so it knows which draft to send.

---

## 5  What’s under the hood?

| Layer | Job |
|-------|-----|
| **gmail-autoauth-mcp** | Node server that logs in via OAuth and exposes `search_emails`, `read_email`, `send_email` tools |
| **langchain-mcp-adapters** | Launches the server with `npx`, wraps each tool as a LangChain `Tool` |
| **LangChain REACT agent** | Chooses tools via Thought/Action/Observation loop |
| **In-memory history** | Remembers draft ⇢ “yes” chain, wiped on exit for privacy |

---

## 6  Common commands

| Task | Command |
|------|---------|
| Upgrade Python packages | `pip install --upgrade -r requirements.txt` |
| Revoke Google token & re‑auth | Delete `%USERPROFILE%\.gmail-mcp\credentials.json` then rerun the script |
| Remove secrets from memory | Close the terminal (secrets live only in `.env`) |

---

## 7  Security notes

* Uses a **refresh token**, never your Gmail password. Revoke anytime in Google Account → Security → Third‑party apps.  
* `.env` is in `.gitignore`; never commit your keys.  
* Human‑in‑the‑loop: the system prompt **always** asks before sending an email.

Enjoy inbox zen! If anything breaks, open an issue or ping me. 💌