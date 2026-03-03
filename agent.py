from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, NOT_GIVEN
from livekit.plugins import google, noise_cancellation
import os
import sys
import subprocess
import asyncio
from mem0 import AsyncMemoryClient
import logging
import json
import httpx
from typing import Optional

from get_weather import get_current_weather
from get_current_time_date import get_current_date_time
from get_web_search import web_search
from prompts import SESSION_INSTRUCTION, AGENT_INSTRUCTION
from system_control import system_control
from get_spotify import spotify_control
from get_news import fetch_news
from youtube_music_control import youtube_music_control
from open_application import open_application, assistant_open_command, close_application, list_running_applications, assistant_list_command

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or NOT_GIVEN

# Validate API key
if not GOOGLE_API_KEY:
    logging.error("GOOGLE_API_KEY not found in environment variables!")
    raise ValueError("GOOGLE_API_KEY is required")


class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                api_key=GOOGLE_API_KEY,
                model="gemini-2.0-flash-exp",
                voice="Charon",
                temperature=0.6,
            ),
            tools=[
                get_current_weather,
                web_search,
                get_current_date_time,
                system_control,
                spotify_control,
                fetch_news,
                youtube_music_control,
                open_application,
                assistant_open_command,
                close_application,
                list_running_applications,
                assistant_list_command,
            ],
            chat_ctx=chat_ctx,
        )


async def entrypoint(ctx: agents.JobContext):
    # Define shutdown hook function
    async def shutdown_hook(
        chat_ctx: "ChatContext", 
        mem0: "Optional[AsyncMemoryClient]", 
        memory_str: str
    ):
        logging.info("Shutting down the agent session...")

        conversation_memories = []
        preference_memories = []

        for item in chat_ctx.items:
            # Extract message content
            content_str = ""
            # Safely get content using getattr with default empty string
            content = getattr(item, "content", "")
            if content:
                if isinstance(content, list):
                    content_str = "".join(map(str, content))
                else:
                    content_str = str(content)
            else:
                content_str = str(item)

            if not content_str.strip():
                continue

            # Skip already stored
            if memory_str and memory_str in content_str:
                continue

            # Safely get role using getattr with default None
            role = getattr(item, "role", None)
            if role and role in ["user", "assistant"]:
                # Normal conversation log
                conversation_memories.append(f"{role}: {content_str.strip()}")

                # Extract preferences from user messages
                if role == "user" and any(
                    kw in content_str.lower()
                    for kw in ["like", "love", "prefer", "enjoy", "hate", "dislike"]
                ):
                    preference_memories.append(content_str.strip())

        # Print conversation to console
        if conversation_memories:
            print("\n=== Conversation log ===")
            for msg in conversation_memories:
                print(msg)
            print("========================\n")

        # Save organized memories in correct Mem0 format
        if conversation_memories and mem0 is not None:
            try:
                await mem0.add(
                    conversation_memories, user_id="RamX", category="conversation"
                )
                logging.info("Conversation saved in mem0.")

                if preference_memories:
                    try:
                        await mem0.add(
                            preference_memories, user_id="RamX", category="preferences"
                        )
                        logging.info("Preferences saved in mem0.")
                    except (httpx.HTTPError, Exception) as e:
                        logging.warning(f"Mem0 add preferences failed: {e}")
            except Exception as e:
                logging.warning(f"Mem0 add conversation failed: {e}")

    # Initialize session and variables
    session = AgentSession()
    mem0 = None
    mem0_api_key = None
    user_name = "RamX"
    initial_ctx = ChatContext()
    memory_str = ""
    agent_chat_ctx = None

    try:
        # Initialize Mem0 client with API key if available
        try:
            mem0_api_key = os.getenv("MEM0_API_KEY")
            mem0 = AsyncMemoryClient(api_key=mem0_api_key) if mem0_api_key else AsyncMemoryClient()
        except Exception as e:
            logging.warning(f"Mem0 client init failed, continuing without it: {e}")
            mem0 = None

        # Restore only preferences for cleaner context
        results = []
        if mem0 is not None:
            try:
                results = await mem0.get_all(user_id=user_name, category="preferences")
            except Exception as e:
                logging.warning(f"Mem0 get_all failed, skipping preferences load: {e}")
        if results:
            memories = [result["memory"] for result in results]
            memory_str = json.dumps(memories, indent=2)
            logging.info(f"Loaded preferences: {memory_str}")
            initial_ctx.add_message(
                role="assistant",
                content=f"Here are known facts about the user {user_name}: {memory_str}",
            )

        # Start the agent session
        await session.start(
            room=ctx.room,
            agent=Assistant(chat_ctx=initial_ctx),
            room_input_options=RoomInputOptions(
                noise_cancellation=None,
            ),
        )

        await ctx.connect()
        
        await session.generate_reply(instructions=SESSION_INSTRUCTION)

        # Proper async shutdown callback wrapper
        async def _shutdown_wrapper():
            final_chat_ctx = agent_chat_ctx if agent_chat_ctx is not None else ChatContext()
            await shutdown_hook(final_chat_ctx, mem0, memory_str)
        
        ctx.add_shutdown_callback(_shutdown_wrapper)
        
    except Exception as e:
        logging.error(f"Error in entrypoint: {e}")
        raise


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))