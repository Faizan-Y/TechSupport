# hybrid_slack_bot.py
import os
import asyncio
from dotenv import load_dotenv
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest

from tech_support_agent import create_agents  # your hybrid agents

load_dotenv()

SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

if not SLACK_APP_TOKEN or not SLACK_BOT_TOKEN:
    raise ValueError("⚠️ SLACK_APP_TOKEN and SLACK_BOT_TOKEN must be set in .env")

# Conversation history per user
conversation_sessions = {}

async def handle_message(user_id, channel, text, client: AsyncWebClient, perplexity_agent, openai_agent):
    # Print the incoming message immediately
    print(f"📩 Received from {user_id} in {channel}: {text}")

    history = conversation_sessions.get(user_id, "")
    prompt = f"{history}\nUser: {text}\nAgent:"

    tool_keywords = ["update", "cancel", "reset"]
    if any(k in text.lower() for k in tool_keywords):
        print("🔧 Using OpenAI agent for tool execution")
        reply = await openai_agent.run(prompt)
    else:
        print("💬 Using Perplexity agent for general chat")
        reply = await perplexity_agent.run(prompt)

    reply = str(reply)
    conversation_sessions[user_id] = f"{history}\nUser: {text}\nAgent: {reply}"

    await client.chat_postMessage(channel=channel, text=reply)
    print(f"📤 Replied to {user_id} in {channel}: {reply}")

async def process(client: SocketModeClient, req: SocketModeRequest, perplexity_agent, openai_agent):
    if req.type == "events_api":
        event = req.payload.get("event", {})
        if "bot_id" not in event and "text" in event:
            user_id = event.get("user")
            channel = event.get("channel")
            text = event.get("text")
            await handle_message(user_id, channel, text, client.web_client, perplexity_agent, openai_agent)
        await client.send_socket_mode_response({"envelope_id": req.envelope_id})

async def main():
    # Create agents here (after event loop started)
    print("💡 Initializing hybrid agents...")
    perplexity_agent, openai_agent = create_agents()
    print("✅ Agents ready!")

    client = SocketModeClient(
        app_token=SLACK_APP_TOKEN,
        web_client=AsyncWebClient(token=SLACK_BOT_TOKEN)
    )

    # Use lambda to pass agents to process function
    client.socket_mode_request_listeners.append(
        lambda req: process(client, req, perplexity_agent, openai_agent)
    )

    # Connect without blocking
    loop = asyncio.get_event_loop()
    loop.create_task(client.connect())
    print("✅ Connected to Slack Socket Mode. Listening for messages...")

    # Keep alive
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
