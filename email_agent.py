"""Gmail summariser + reply assistant (LangChain + email-client MCP).

Features
--------
* Natural-language search & summarise of Gmail threads
* Draft / reply to emails – **always asks for confirmation before sending**

Run:
    python email_agent.py
"""

import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()  # pulls vars from .env

SYSTEM_PROMPT = """
You are a helpful Gmail assistant.
When the user asks to send or reply to an email you MUST:
1. Draft the email with the appropriate tool.
2. Show the full draft (to, cc, subject, body) to the user.
3. Ask explicitly: "Send this email? (yes/no)".
4. Only call the send tool if the user answers yes / y / send.
If the user declines, abort sending and report that the email was not sent.
When summarising, be concise.
""".strip()

EMAIL_ENV_VARS = [
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",   # Gmail App Password
    "IMAP_SERVER",
    "SMTP_SERVER",
    "SMTP_PORT",
]


async def build_agent():
    """Launch the email MCP server and wrap its tools in a LangChain agent."""
    # Sanity-check creds
    missing = [v for v in EMAIL_ENV_VARS if not os.getenv(v)]
    if missing:
        raise RuntimeError(
            f"❗️ Missing env vars: {', '.join(missing)}. "
            "Fill them in your .env file."
        )

    client = MultiServerMCPClient(
        {
            "gmail": {
                "command": "email-client",     # console script from the repo
                "args": [],                    # stdio transport by default
                "transport": "stdio",
                "env": {k: os.getenv(k) for k in EMAIL_ENV_VARS},
            }
        }
    )

    tools = await client.get_tools()
    if not tools:
        raise RuntimeError(
            "🚫 email-client started but exposed no tools. "
            "Double-check Gmail credentials / IMAP enabled."
        )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_react_agent(llm, tools)


async def chat_loop() -> None:
    agent = await build_agent()

    print("Ask me about your Gmail (type 'quit' to exit):\n")
    while True:
        user_q = input("> ").strip()
        if user_q.lower() in {"quit", "exit"}:
            break

        result = await agent.ainvoke(
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_q},
                ]
            }
        )

        # langgraph returns {'messages': [...]}; last item is the agent reply
        if isinstance(result, dict) and "messages" in result:
            print("\n" + result["messages"][-1].content + "\n")
        else:
            print("\n" + str(result) + "\n")


def main():
    asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
