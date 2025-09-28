from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import google, noise_cancellation
import os
from mem0 import AsyncMemoryClient
import logging
import json

from get_weather import get_current_weather
from get_current_time_date import get_current_date_time
from get_web_search import web_search
from prompts import SESSION_INSTRUCTION, AGENT_INSTRUCTION
from system_control import system_control
from get_spotify import spotify_control
from get_news import fetch_news
from youtube_music_control import youtube_music_control
from get_open_app import open_app, assistant_command_listener

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class Assistant(Agent):
    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                api_key=GOOGLE_API_KEY,
                model="gemini-2.0-flash-exp",
                voice="Charon",
                temperature=0.8,
            ),
            tools=[
                get_current_weather,
                web_search,
                get_current_date_time,
                system_control,
                spotify_control,
                fetch_news,
                youtube_music_control,
                open_app,
                assistant_command_listener,
            ],
            chat_ctx=chat_ctx,
        )


async def entrypoint(ctx: agents.JobContext):
    async def shutdown_hook(
        chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str
    ):
        logging.info("Shutting down the agent session...")

        conversation_memories = []
        preference_memories = []

        for item in chat_ctx.items:
            # Extract message content
            if hasattr(item, "content"):
                if isinstance(item.content, list):
                    content_str = "".join(map(str, item.content))
                else:
                    content_str = str(item.content)
            else:
                content_str = str(item)

            if not content_str.strip():
                continue

            # Skip already stored
            if memory_str and memory_str in content_str:
                continue

            if hasattr(item, "role") and item.role in ["user", "assistant"]:
                # Normal conversation log
                conversation_memories.append(f"{item.role}: {content_str.strip()}")

                # Extract preferences from user messages
                if item.role == "user" and any(
                    kw in content_str.lower()
                    for kw in ["like", "love", "prefer", "enjoy", "hate", "dislike"]
                ):
                    preference_memories.append(content_str.strip())

        # Save organized memories
        if conversation_memories:
            await mem0.add(
                conversation_memories, user_id="RamX", category="conversation"
            )
            logging.info("Conversation saved in mem0.")

        if preference_memories:
            await mem0.add(preference_memories, user_id="RamX", category="preferences")
            logging.info("Preferences saved in mem0.")

    session = AgentSession()

    mem0 = AsyncMemoryClient()
    user_name = "RamX"
    initial_ctx = ChatContext()
    memory_str = ""

    # Restore only preferences (cleaner context)
    results = await mem0.get_all(user_id=user_name, category="preferences")

    if results:
        memories = [result["memory"] for result in results]
        memory_str = json.dumps(memories, indent=2)
        logging.info(f"Loaded preferences: {memory_str}")
        initial_ctx.add_message(
            role="assistant",
            content=f"Here are known facts about the user {user_name}: {memory_str}",
        )

    await session.start(
        room=ctx.room,
        agent=Assistant(chat_ctx=initial_ctx),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(instructions=SESSION_INSTRUCTION)

    ctx.add_shutdown_callback(
        lambda: shutdown_hook(session._agent.chat_ctx, mem0, memory_str)
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
