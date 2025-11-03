from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext
from livekit.plugins import google, noise_cancellation
import os
import sys
import subprocess
import asyncio
from mem0 import AsyncMemoryClient
import logging
import json
import httpx

from get_weather import get_current_weather
from get_current_time_date import get_current_date_time
from get_web_search import web_search
from prompts import SESSION_INSTRUCTION, AGENT_INSTRUCTION
from system_control import system_control
from get_spotify import spotify_control
from get_news import fetch_news
from youtube_music_control import youtube_music_control
from open_application import open_application, assistant_open_command, close_application
from set_avatar_expression import set_avatar_expression

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
                open_application,
                close_application,
                assistant_open_command,
                set_avatar_expression,
            ],
            chat_ctx=chat_ctx,
        )

async def entrypoint(ctx: agents.JobContext):
    async def shutdown_hook(
        chat_ctx: ChatContext, mem0: AsyncMemoryClient, memory_str: str, avatar_proc: subprocess.Popen | None, expr_task: asyncio.Task | None
    ):
        logging.info("Shutting down the agent session...")
        # Stop desktop avatar process if started
        try:
            if avatar_proc and avatar_proc.poll() is None:
                avatar_proc.terminate()
        except Exception as e:
            logging.warning(f"Failed to terminate desktop avatar: {e}")
        # Cancel expression watcher
        try:
            if expr_task and not expr_task.done():
                expr_task.cancel()
        except Exception:
            pass

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

        # Print conversation to console
        if conversation_memories:
            print("\n=== Conversation log ===")
            for msg in conversation_memories:
                print(msg)
            print("========================\n")

        # Save organized memories in correct Mem0 format
        if conversation_memories:
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

    session = AgentSession()
    # Initialize Mem0 client with API key if available
    try:
        mem0_api_key = os.getenv("MEM0_API_KEY")
        mem0 = AsyncMemoryClient(api_key=mem0_api_key) if mem0_api_key else AsyncMemoryClient()
    except Exception as e:
        logging.warning(f"Mem0 client init failed, continuing without it: {e}")
        mem0 = None
    user_name = "RamX"
    initial_ctx = ChatContext()
    memory_str = ""

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
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()
    # Start desktop avatar UI
    avatar_proc = None
    try:
        avatar_path = os.path.join(os.path.dirname(__file__), "avatar", "desktop_avatar.py")
        avatar_proc = subprocess.Popen([sys.executable, "-u", avatar_path])
        logging.info("Desktop avatar started")
    except Exception as e:
        logging.warning(f"Failed to start desktop avatar: {e}")

    await session.generate_reply(instructions=SESSION_INSTRUCTION)

    # Start background watcher to trigger avatar expressions from assistant messages
    async def _expression_watcher(chat_ctx: ChatContext):
        last_idx = 0
        while True:
            try:
                items = list(chat_ctx.items)
                if last_idx < len(items):
                    new_items = items[last_idx:]
                    last_idx = len(items)
                    for it in new_items:
                        try:
                            role = getattr(it, "role", None)
                            # Only watch assistant messages for expressions
                            if role != "assistant":
                                continue
                            content = getattr(it, "content", "")
                            if isinstance(content, list):
                                text = "".join(map(str, content))
                            else:
                                text = str(content)
                            
                            if not text or not text.strip():
                                continue
                                
                            low = text.lower()
                            logging.info(f"[Expression Watcher] Checking: {text[:100]}...")
                            
                            # Map keywords to expressions
                            expr = None
                            dur = 1.2
                            if any(k in low for k in ["winking face", "wink", "😉"]):
                                expr = "wink"
                                dur = 1.2
                            elif any(k in low for k in ["open mouth smile", "big smile", "😀", "😃", "grin"]):
                                expr = "smile_open"
                                dur = 1.5
                            elif any(k in low for k in ["cool", "sunglasses", "😎", "shades"]):
                                expr = "cool"
                                dur = 1.5
                            elif any(k in low for k in ["happy", "joy", "joyful", "😊", "😄", "excited", "tears of joy", "awesome"]):
                                expr = "happy"
                                dur = 1.5
                            elif any(k in low for k in ["sad", "crying", "😢", "😭", "unhappy"]):
                                expr = "sad"
                                dur = 2.0
                            elif any(k in low for k in ["surprised", "shock", "😲", "😮", "amazed", "wow"]):
                                expr = "surprised"
                                dur = 1.3
                            elif any(k in low for k in ["angry", "mad", "😠", "😡", "furious"]):
                                expr = "angry"
                                dur = 1.8
                            elif any(k in low for k in ["sleepy", "tired", "😴", "yawn", "drowsy"]):
                                expr = "sleepy"
                                dur = 2.5
                            elif any(k in low for k in ["thinking", "hmm", "🤔", "pondering", "let me think"]):
                                expr = "thinking"
                                dur = 2.0
                            elif any(k in low for k in ["love", "heart", "😍", "❤️", "💕", "adore"]):
                                expr = "love"
                                dur = 2.0
                            elif any(k in low for k in ["neutral face", "back to normal", "neutral"]):
                                expr = "neutral"
                                dur = 0.6
                            if expr:
                                logging.info(f"[Expression Watcher] Detected '{expr}' expression, triggering for {dur}s")
                                try:
                                    result = await set_avatar_expression(expr=expr, duration=dur)
                                    logging.info(f"[Expression Watcher] Result: {result}")
                                except Exception as e:
                                    logging.warning(f"[Expression Watcher] set_avatar_expression failed: {e}")
                        except Exception:
                            pass
                await asyncio.sleep(0.1)  # Check every 100ms for faster response
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)

    expr_task = asyncio.create_task(_expression_watcher(session._agent.chat_ctx))

    ctx.add_shutdown_callback(
        lambda: shutdown_hook(session._agent.chat_ctx, mem0, memory_str, avatar_proc, expr_task)
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
