import time
import subprocess
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
def open_application(app_name: str) -> str:
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
def assistant_open_command(command: str) -> str:
    """
    Detects phrases like "open <app>" and triggers open_application.
    Returns a user-facing verbal response string.
    """
    if not command:
        return ""
    text = command.strip()
    lower = text.lower()
    if "open" in lower:
        # extract best-effort app name after the first occurrence of 'open'
        try:
            idx = lower.index("open")
            candidate = text[idx + len("open"):].strip().strip('"\' ')
            if candidate:
                return open_application(candidate)
        except Exception:
            pass
    return ""
