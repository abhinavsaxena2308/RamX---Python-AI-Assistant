"""
Test script to cycle through all avatar expressions
Make sure the avatar is running first: python -m avatar.desktop_avatar
"""
import asyncio
import sys
from set_avatar_expression import set_avatar_expression


async def test_all_expressions():
    """Test all available expressions with descriptions"""
    
    expressions = [
        ("neutral", 1, "Neutral - Default expression"),
        ("wink", 3, "Wink - Playful winking face"),
        ("smile_open", 5, "Smile Open - Big happy smile with open mouth"),
        ("cool", 5, "Cool - Sunglasses for a cool look"),
        ("happy", 5, "Happy - Joyful expression"),
        ("sad", 5, "Sad - Sad frown"),
        ("surprised", 5, "Surprised - Wide eyes and open mouth"),
        ("angry", 5, "Angry - Angry eyebrows and gritted teeth"),
        ("sleepy", 5, "Sleepy - Tired with zzz's"),
        ("thinking", 5, "Thinking - Contemplative with thought bubble"),
        ("love", 5, "Love - Heart eyes"),
    ]
    
    print("=" * 60)
    print("AVATAR EXPRESSION TEST")
    print("=" * 60)
    print("\nMake sure the avatar is running!")
    print("Start with: python -m avatar.desktop_avatar\n")
    print("=" * 60)
    
    await asyncio.sleep(2)
    
    for expr, duration, description in expressions:
        print(f"\n▶ Testing: {description}")
        result = await set_avatar_expression(expr, duration)
        print(f"  Result: {result}")
        await asyncio.sleep(duration + 0.5)  # Wait for expression to complete
    
    print("\n" + "=" * 60)
    print("✓ All expressions tested!")
    print("=" * 60)


async def test_single_expression(expr_name: str):
    """Test a single expression"""
    print(f"\n▶ Testing expression: {expr_name}")
    result = await set_avatar_expression(expr_name, 3.0)
    print(f"  Result: {result}")
    await asyncio.sleep(3.5)


async def interactive_test():
    """Interactive mode to test expressions manually"""
    print("=" * 60)
    print("INTERACTIVE EXPRESSION TESTER")
    print("=" * 60)
    print("\nAvailable expressions:")
    print("  1. neutral    2. wink       3. smile_open")
    print("  4. cool       5. happy      6. sad")
    print("  7. surprised  8. angry      9. sleepy")
    print("  10. thinking  11. love")
    print("\nType expression name or number (or 'all' to test all, 'quit' to exit)")
    print("=" * 60)
    
    expr_map = {
        "1": "neutral", "2": "wink", "3": "smile_open",
        "4": "cool", "5": "happy", "6": "sad",
        "7": "surprised", "8": "angry", "9": "sleepy",
        "10": "thinking", "11": "love"
    }
    
    while True:
        try:
            choice = input("\n▶ Enter expression: ").strip().lower()
            
            if choice in ["quit", "exit", "q"]:
                print("Exiting...")
                break
            elif choice == "all":
                await test_all_expressions()
            elif choice in expr_map:
                await test_single_expression(expr_map[choice])
            elif choice in ["neutral", "wink", "smile_open", "cool", "happy", "sad", 
                          "surprised", "angry", "sleepy", "thinking", "love"]:
                await test_single_expression(choice)
            else:
                print(f"❌ Unknown expression: {choice}")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific expression from command line
        expr = sys.argv[1].lower()
        if expr == "all":
            asyncio.run(test_all_expressions())
        else:
            asyncio.run(test_single_expression(expr))
    else:
        # Interactive mode
        asyncio.run(interactive_test())
