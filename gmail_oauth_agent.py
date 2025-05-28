"""
Gmail assistant (LangChain + Gmail AutoAuth MCP)
-----------------------------------------------
"""

import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# ──────────────────── CONFIG ──────────────────── #
load_dotenv()                                     # loads .env

HOME          = Path.home()
MCP_DIR       = HOME / ".gmail-mcp"
OAUTH_JSON    = MCP_DIR / "gcp-oauth.keys.json"
CREDS_JSON    = MCP_DIR / "credentials.json"

SYSTEM_PROMPT = (
    "You are a helpful Gmail assistant. "
    "When the user asks to send or reply, you MUST:\n"
    "  1. Draft the email.\n"
    "  2. Show the full draft (to, subject, body).\n"
    "  3. Ask: 'Send this email? (yes/no)'.\n"
    "  4. Only send if the user confirms.\n"
    "Otherwise, summarise emails concisely."
)

# ──────────────────── HELPERS ──────────────────── #
def find_npx() -> str:
    """Return path to npx (npx.cmd on Windows) or exit if not found."""
    exe = "npx.cmd" if platform.system() == "Windows" else "npx"
    path = shutil.which(exe)
    if not path:
        sys.exit("❗  Node.js (npx) not found on PATH. Install Node.js and restart.")
    return path


def write_oauth_json_if_needed():
    """Generate gcp-oauth.keys.json from .env values (one-off)."""
    if OAUTH_JSON.exists():
        return

    cid     = os.getenv("GOOGLE_CLIENT_ID")
    secret  = os.getenv("GOOGLE_CLIENT_SECRET")
    project = os.getenv("GOOGLE_PROJECT_ID", "gmail-assistant")

    if not (cid and secret):
        sys.exit("❗  Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env first.")

    MCP_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "installed": {
            "client_id":     cid,
            "project_id":    project,
            "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
            "token_uri":     "https://oauth2.googleapis.com/token",
            "client_secret": secret,
            "redirect_uris": ["http://localhost"],
        }
    }
    OAUTH_JSON.write_text(json.dumps(data, indent=2))
    print(f"✅  Wrote {OAUTH_JSON}")


def run_oauth_flow():
    """Launch one-time Google consent flow (opens browser)."""
    print("🔑  Launching Gmail OAuth flow — a browser tab will open…")
    subprocess.run(
        [find_npx(), "-y", "@gongrzhe/server-gmail-autoauth-mcp", "auth"],
        check=True,
    )

    if CREDS_JSON.exists():
        print("✅  Google consent completed.")
    else:
        sys.exit("⚠️  Consent aborted — credentials.json not created.")


# ──────────────────── LANGCHAIN AGENT ──────────────────── #
async def build_agent():
    client = MultiServerMCPClient(
        {
            "gmail": {
                "command": find_npx(),
                "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()
    if not tools:
        sys.exit("🚫 Gmail MCP server started but exposed no tools.")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_react_agent(llm, tools)


# ──────────────────── CLI CHAT LOOP ──────────────────── #
async def main():
    write_oauth_json_if_needed()
    if not CREDS_JSON.exists():
        run_oauth_flow()

    agent = await build_agent()

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("\nAsk me about your Gmail (type 'quit' to exit):\n")

    while True:
        user_text = input("> ").strip()
        if user_text.lower() in {"quit", "exit"}:
            break

        history.append({"role": "user", "content": user_text})
        result = await agent.ainvoke({"messages": history})

        assistant_msg = result["messages"][-1]
        print("\n" + assistant_msg.content + "\n")

        # Append any new messages (assistant reply + tool traces)
        history.extend(result["messages"][len(history):])


if __name__ == "__main__":
    asyncio.run(main())
