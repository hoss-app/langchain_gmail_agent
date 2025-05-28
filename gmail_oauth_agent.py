# gmail_oauth_agent.py
import asyncio, json, os, subprocess, sys, time
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

HOME = Path.home()
MCP_DIR = HOME / ".gmail-mcp"
OAUTH_JSON = MCP_DIR / "gcp-oauth.keys.json"
CREDS_JSON = MCP_DIR / "credentials.json"

SYSTEM_PROMPT = (
    "You are a helpful Gmail assistant. "
    "When the user asks to send or reply, DRAFT first, show it, then ask "
    "'Send this email? (yes/no)'. Only send if the user confirms."
)

# ------------------------------------------------------------------ #
# 1.  Ensure gcp-oauth.keys.json exists (generated from .env)        #
# ------------------------------------------------------------------ #
def write_oauth_json_if_needed():
    if OAUTH_JSON.exists():
        return
    cid, secret = os.getenv("GOOGLE_CLIENT_ID"), os.getenv("GOOGLE_CLIENT_SECRET")
    if not (cid and secret):
        sys.exit("❗  Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env first.")
    MCP_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "installed": {
            "client_id": cid,
            "client_secret": secret,
            "project_id": os.getenv("GOOGLE_PROJECT_ID", "gmail-agent"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    OAUTH_JSON.write_text(json.dumps(data, indent=2))
    print(f"✅  Wrote {OAUTH_JSON}")


# ------------------------------------------------------------------ #
# 2.  One-time OAuth flow (opens browser)                            #
# ------------------------------------------------------------------ #
import shutil, platform, subprocess, sys

def run_oauth_flow():
    # Pick the right executable on Windows (npx.cmd) vs *nix (npx)
    npx_exe = "npx.cmd" if platform.system() == "Windows" else "npx"
    if not shutil.which(npx_exe):
        sys.exit(
            "❗  npx not found on PATH. Install Node.js (includes npx) "
            "and restart your terminal."
        )

    print("🔑  Launching Gmail OAuth flow — a browser tab will open…")
    proc = subprocess.Popen(
        [npx_exe, "-y", "@gongrzhe/server-gmail-autoauth-mcp", "auth"],
        cwd=Path.cwd(),
        shell=False,
    )
    proc.wait()

    if CREDS_JSON.exists():
        print("✅  Google consent completed.")
    else:
        sys.exit("⚠️  Credentials not created; OAuth flow aborted.")

# ------------------------------------------------------------------ #
# 3.  Build LangChain agent                                          #
# ------------------------------------------------------------------ #
async def build_agent():
    client = MultiServerMCPClient(
        {
            "gmail": {
                "command": "npx",
                "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"],
                "transport": "stdio",
            }
        }
    )
    tools = await client.get_tools()
    if not tools:
        sys.exit("🚫 Gmail MCP server started but no tools exposed.")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_react_agent(llm, tools)


# ------------------------------------------------------------------ #
# 4.  Main chat loop                                                 #
# ------------------------------------------------------------------ #
async def main():
    write_oauth_json_if_needed()
    if not CREDS_JSON.exists():
        run_oauth_flow()

    agent = await build_agent()
    print("\nAsk me about your Gmail (type 'quit' to exit):\n")
    while True:
        q = input("> ").strip()
        if q.lower() in {"quit", "exit"}:
            break
        result = await agent.ainvoke(
            {"messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ]}
        )
        print("\n" + result["messages"][-1].content + "\n")


if __name__ == "__main__":
    asyncio.run(main())
