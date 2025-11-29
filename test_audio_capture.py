"""
Test if Windows audio capture is working
"""
from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
import time
import pyttsx3
import threading

def test_audio_monitoring():
    """Test if we can capture system audio"""
    print("=" * 60)
    print("AUDIO CAPTURE TEST")
    print("=" * 60)
    
    # Initialize audio meter
    try:
        # Get all audio devices and find the default output
        devices = AudioUtilities.GetAllDevices()
        default_device = None
        
        print(f"Found {len(devices)} audio devices")
        
        # Find default playback device (output device)
        for device in devices:
            try:
                # Check if it's an output device (ID starts with {0.0.0) and is Active
                if (device.id.startswith('{0.0.0') and 
                    str(device.state) == 'AudioDeviceState.Active'):
                    default_device = device
                    print(f"Found active output: {device.FriendlyName}")
                    break
            except Exception as e:
                continue
        
        if default_device:
            # Get the audio meter interface
            interface = default_device._dev.Activate(
                IAudioMeterInformation._iid_, CLSCTX_ALL, None
            )
            meter = cast(interface, POINTER(IAudioMeterInformation))
            print(f"✓ Audio meter initialized: {default_device.FriendlyName}")
        else:
            print("✗ No active audio device found")
            return
            
    except Exception as e:
        print(f"✗ Failed to initialize audio meter: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("TEST 1: Silent baseline")
    print("=" * 60)
    print("Measuring silence for 2 seconds...")
    
    for i in range(20):
        peak = meter.GetPeakValue()
        print(f"  Peak {i+1}: {peak:.4f}")
        time.sleep(0.1)
    
    print("\n" + "=" * 60)
    print("TEST 2: Text-to-Speech")
    print("=" * 60)
    print("Starting TTS in 1 second... Watch for peak values!")
    time.sleep(1)
    
    # Start TTS in background
    def speak():
        engine = pyttsx3.init()
        engine.setProperty('volume', 1.0)
        engine.say("Testing audio capture with text to speech")
        engine.runAndWait()
    
    tts_thread = threading.Thread(target=speak)
    tts_thread.start()
    
    # Monitor audio for 5 seconds
    max_peak = 0.0
    peaks_detected = 0
    
    for i in range(50):
        peak = meter.GetPeakValue()
        if peak > 0.01:
            peaks_detected += 1
            max_peak = max(max_peak, peak)
            print(f"  Peak {i+1}: {peak:.4f} {'🔊' if peak > 0.1 else '🔉' if peak > 0.05 else ''}")
        else:
            print(f"  Peak {i+1}: {peak:.4f}")
        time.sleep(0.1)
    
    tts_thread.join()
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Max peak detected: {max_peak:.4f}")
    print(f"Peaks above 0.01: {peaks_detected}/50")
    
    if max_peak > 0.1:
        print("✓ AUDIO CAPTURE WORKING! Lip-sync should work.")
    elif max_peak > 0.01:
        print("⚠ Audio detected but very quiet. Increase volume or check audio settings.")
    else:
        print("✗ NO AUDIO DETECTED!")
        print("\nPossible issues:")
        print("1. Speakers are muted or volume is too low")
        print("2. Audio is playing through different device (headphones vs speakers)")
        print("3. Windows audio settings need adjustment")
        print("\nTry:")
        print("- Right-click speaker icon → Open Sound Settings")
        print("- Ensure correct output device is selected")
        print("- Increase volume to 50%+")
        print("- Play music and check if avatar mouth moves")

if __name__ == "__main__":
    try:
        test_audio_monitoring()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
