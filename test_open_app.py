import asyncio
from open_application import open_application, close_application, list_running_applications

async def test():
    print("Testing open_application...")
    result = await open_application("calculator")
    print(f"Open result: {result}")
    
    print("Testing list_running_applications...")
    result = await list_running_applications()
    print(f"List result: {result}")
    
    print("Testing close_application...")
    result = await close_application("calculator")
    print(f"Close result: {result}")
    
    print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test())