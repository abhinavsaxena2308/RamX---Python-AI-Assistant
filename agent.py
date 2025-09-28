from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google, noise_cancellation
import os

# Import your custom tools
from get_weather import get_current_weather
from get_current_time_date import get_current_date_time
from get_web_search import web_search
from prompts import SESSION_INSTRUCTION, AGENT_INSTRUCTION
from system_control import system_control
from get_spotify import spotify_control
from get_news import fetch_news  
from youtube_music_control import youtube_music_control

# Load environment variables
load_dotenv()

API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class Assistant(Agent):
    def __init__(self) -> None:
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
                youtube_music_control
            ],
        )

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` instead for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint)
    )
