import time
import subprocess
import os
from typing import Optional
import pyautogui
from livekit.agents import function_tool

# Helper: Basic app name normalization
COMMON_ALIASES = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "microsoft edge": "Microsoft Edge",
    "calc": "Calculator",
    "notepad++": "Notepad++",
}

# Optional fallback commands for popular apps
FALLBACK_CMDS = {
    "chrome": ["cmd", "/c", "start", "", "chrome"],
    "google chrome": ["cmd", "/c", "start", "", "chrome"],
    "edge": ["cmd", "/c", "start", "", "msedge"],
    "microsoft edge": ["cmd", "/c", "start", "", "msedge"],
    "notepad": ["cmd", "/c", "start", "", "notepad"],
    "calculator": ["cmd", "/c", "start", "", "calc"],
    "word": ["cmd", "/c", "start", "", "winword"],
    "excel": ["cmd", "/c", "start", "", "excel"],
    "powerpoint": ["cmd", "/c", "start", "", "powerpnt"],
    "paint": ["cmd", "/c", "start", "", "mspaint"],
    "telegram": ["cmd", "/c", "start", "", "telegram"],
}

# Process names for closing applications
APP_PROCESS_NAMES = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
    "calc": "CalculatorApp.exe",
    "word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
    "paint": "mspaint.exe",
    "notepad++": "notepad++.exe",
    "spotify": "Spotify.exe",
    "discord": "Discord.exe",
    "vscode": "Code.exe",
    "visual studio code": "Code.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "telegram": "Telegram.exe",
}


def _normalize(name: str) -> str:
    n = name.strip().lower()
    return COMMON_ALIASES.get(n, name.strip())


def _speak_ack(text: str) -> str:
    # Returning text allows LiveKit's voice to speak it.
    return text


def _try_start_menu_launch(app_name: str) -> None:
    # Focus Start menu, type the app name, press Enter
    # Add small delays to allow UI to catch up
    pyautogui.FAILSAFE = False
    pyautogui.press("win")
    time.sleep(0.35)
    pyautogui.typewrite(app_name, interval=0.02)
    time.sleep(0.9)
    pyautogui.press("enter")


def _fallback_known_apps(app_name: str) -> bool:
    key = app_name.strip().lower()
    if key in FALLBACK_CMDS:
        try:
            subprocess.Popen(FALLBACK_CMDS[key], shell=False)
            return True
        except Exception:
            return False
    return False


@function_tool()
async def open_application(app_name: str) -> str:
    """
    Opens a Windows application using the Start Menu typing approach.
    If the app can't be opened, returns an apologetic verbal message.
    """
    if not app_name or not app_name.strip():
        return _speak_ack("Please specify an app to open.")

    norm = _normalize(app_name)
    print(f"[Assistant]: Trying to open {norm}")

    try:
        # Verbal acknowledgement first
        ack = _speak_ack(f"Opening {norm}...")
        # Attempt Start Menu flow
        _try_start_menu_launch(norm)
        # Small buffer; if it fails silently we provide a fallback
        time.sleep(0.6)
        return ack
    except Exception:
        # Fallback to known subprocess starts for common apps
        if _fallback_known_apps(norm):
            return _speak_ack(f"Opening {norm}...")
        # Final verbal failure
        return _speak_ack(f"Sorry, I couldn't find {norm} on this system.")


@function_tool()
async def close_application(app_name: str) -> str:
    """
    Closes a Windows application by terminating its process.
    Returns a verbal confirmation or error message.
    """
    if not app_name or not app_name.strip():
        return _speak_ack("Please specify an app to close.")

    norm = _normalize(app_name)
    key = norm.strip().lower()
    
    # Get the process name for the app
    process_name = APP_PROCESS_NAMES.get(key)
    
    if not process_name:
        # Try using the normalized name with .exe extension
        process_name = f"{norm}.exe"
    
    print(f"[Assistant]: Trying to close {norm} (process: {process_name})")
    
    try:
        # First check if the process is running
        check_cmd = f'tasklist /FI "IMAGENAME eq {process_name}" 2>NUL | find /I /N "{process_name}"'
        check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if process_name.lower() not in check_result.stdout.lower():
            return _speak_ack(f"{norm} is not currently running.")
        
        # Use taskkill command to close the application
        kill_cmd = ["taskkill", "/F", "/IM", process_name]
        result = subprocess.run(kill_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return _speak_ack(f"Closed {norm}.")
        else:
            # Try alternative process names for some apps
            if key in ["calculator", "calc"]:
                # Try both Calculator.exe and CalculatorApp.exe
                for alt_name in ["Calculator.exe", "CalculatorApp.exe", "win32calc.exe"]:
                    try:
                        alt_result = subprocess.run(["taskkill", "/F", "/IM", alt_name], 
                                                   capture_output=True, text=True)
                        if alt_result.returncode == 0:
                            return _speak_ack(f"Closed {norm}.")
                    except Exception:
                        continue
            
            return _speak_ack(f"Could not close {norm}. It may not be running.")
    except Exception as e:
        print(f"[Error closing {norm}]: {str(e)}")
        return _speak_ack(f"Failed to close {norm}.")


@function_tool()
async def assistant_open_command(command: str) -> str:
    """
    Detects phrases like "open <app>" or "close <app>" and triggers the appropriate function.
    Returns a user-facing verbal response string.
    """
    if not command:
        return ""
    text = command.strip()
    lower = text.lower()
    
    # Check for close command
    if "close" in lower:
        try:
            idx = lower.index("close")
            candidate = text[idx + len("close"):].strip().strip('"\' ')
            if candidate:
                return await close_application(candidate)
        except Exception:
            pass
    
    # Check for open command
    if "open" in lower:
        try:
            idx = lower.index("open")
            candidate = text[idx + len("open"):].strip().strip('"\' ')
            if candidate:
                return await open_application(candidate)
        except Exception:
            pass
    
    return ""
