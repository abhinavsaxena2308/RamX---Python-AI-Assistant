from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, INTRODUCTION_PROMPT
from tools import search_web, get_current_datetime, get_weather
import asyncio

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Charon",  # ✅ Hindi-friendly voice
                temperature=0.8,
            ),
            tools=[search_web, get_current_datetime, get_weather],
        )


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Interrupt flag
    interrupt_flag = False

    # Interrupt checker function
    async def interrupt_checker():
        nonlocal interrupt_flag
        try:
            async for transcript in session.stream_user_transcription():
                if transcript.text and "jarvis wait" in transcript.text.lower():
                    print("🛑 Interrupt detected! Stopping current speech...")
                    interrupt_flag = True
                    await session.stop_generation()
                    break
        except Exception as e:
            print(f"⚠️ Interrupt checker error: {e}")

    # Start interrupt checker in background
    asyncio.create_task(interrupt_checker())

    await ctx.connect()
    await asyncio.sleep(0.5)  # small delay to reduce lag at startup

    try:
        await session.generate_reply(
            instructions=INTRODUCTION_PROMPT,
            timeout=60
        )
    except agents.llm.realtime.RealtimeError as e:
        print(f"⚠️ Introduction generation failed: {e}")

    # ✅ Start normal session for user queries
    try:
        await session.generate_reply(
            instructions=SESSION_INSTRUCTION,
            timeout=60
        )
    except agents.llm.realtime.RealtimeError as e:
        print(f"⚠️ Realtime generation failed: {e}")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
