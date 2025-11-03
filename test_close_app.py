"""
Test script to verify close_application functionality
"""
import asyncio
import time
from open_application import close_application, open_application


async def test_close():
    """Test closing applications"""
    
    print("=" * 60)
    print("TESTING CLOSE APPLICATION FUNCTIONALITY")
    print("=" * 60)
    
    # Test 1: Try to close an app that's not running
    print("\n1. Testing close on non-running app (should say not running):")
    result = await close_application("notepad")
    print(f"   Result: {result}")
    
    # Test 2: Open notepad and then close it
    print("\n2. Opening notepad...")
    result = await open_application("notepad")
    print(f"   Result: {result}")
    
    await asyncio.sleep(2)  # Wait for notepad to open
    
    print("\n3. Closing notepad...")
    result = await close_application("notepad")
    print(f"   Result: {result}")
    
    # Test 3: Try to close calculator
    print("\n4. Opening calculator...")
    result = await open_application("calculator")
    print(f"   Result: {result}")
    
    await asyncio.sleep(2)  # Wait for calculator to open
    
    print("\n5. Closing calculator...")
    result = await close_application("calculator")
    print(f"   Result: {result}")
    
    # Test 4: Test Telegram
    print("\n6. Testing Telegram open/close...")
    result = await open_application("telegram")
    print(f"   Result: {result}")
    
    await asyncio.sleep(3)
    
    result = await close_application("telegram")
    print(f"   Result: {result}")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_close())
