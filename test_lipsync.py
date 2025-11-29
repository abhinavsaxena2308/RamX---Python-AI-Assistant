"""
Test script to verify avatar lip-sync with text-to-speech
"""
import pyttsx3
import time

def test_lipsync():
    """Test avatar lip-sync by speaking some text"""
    engine = pyttsx3.init()
    
    # Configure voice
    engine.setProperty('rate', 150)  # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    print("Testing avatar lip-sync...")
    print("Watch the avatar's mouth while speaking!\n")
    
    test_phrases = [
        "Hello! I am RamLal, your AI assistant.",
        "The avatar should move its mouth when I speak.",
        "This is a test of the lip sync functionality.",
        "Amazing! The mouth animation is working perfectly!"
    ]
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"{i}. Speaking: {phrase}")
        engine.say(phrase)
        engine.runAndWait()
        time.sleep(1)
    
    print("\nLip-sync test completed!")
    print("Did you see the avatar's mouth moving? If yes, it's working!")

if __name__ == "__main__":
    try:
        test_lipsync()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. Avatar is running (python avatar/desktop_avatar.py)")
        print("2. pyttsx3 is installed (pip install pyttsx3)")
        print("3. Your speakers are on and volume is up")
