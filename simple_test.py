import asyncio
from open_application import list_running_applications

async def test():
    result = await list_running_applications()
    print(f"List result: {result}")

asyncio.run(test())