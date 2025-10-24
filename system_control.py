from livekit.agents import function_tool   


@function_tool()
async def system_control(command: str) -> str:
    """
    Execute basic system control commands like 'open notepad', 'close browser', etc.
    """
    import subprocess
    import time
    import pyautogui
    import os
    import webbrowser

    try:
        command = command.lower()
        if "open notepad" in command:
            subprocess.Popen(['notepad.exe'])
            return "Notepad opened."
        elif "close notepad" in command:
            os.system("taskkill /f /im notepad.exe")
            return "Notepad closed."
        elif "open browser" in command:
            subprocess.Popen(['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'])
            return "Browser opened."
        elif "close browser" in command:
            os.system("taskkill /f /im chrome.exe")
            return "Browser closed."
        elif "minimize window" in command:
            pyautogui.hotkey('win', 'down')
            return "Window minimized."
        elif "maximize window" in command:
            pyautogui.hotkey('win', 'up')
            return "Window maximized."
        else:
            return "Command not recognized. Please try again."

    except Exception as e:
        return f"An error occurred while executing the command: {e}"

