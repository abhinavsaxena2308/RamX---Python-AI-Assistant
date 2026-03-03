#!/usr/bin/env python3

print("Testing imports...")

try:
    import aiohttp
    print("aiohttp imported successfully")
except Exception as e:
    print(f"Failed to import aiohttp: {e}")

try:
    from livekit import agents
    print("livekit.agents imported successfully")
except Exception as e:
    print(f"Failed to import livekit.agents: {e}")

try:
    import typing
    print(f"typing module: {typing}")
except Exception as e:
    print(f"Failed to import typing: {e}")

print("Test completed.")