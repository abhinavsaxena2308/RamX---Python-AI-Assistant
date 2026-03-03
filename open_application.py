import time
import subprocess
<<<<<<< HEAD
import os
from typing import Optional
import pyautogui
from livekit.agents import function_tool
=======
import asyncio
from typing import Optional
import pyautogui
from livekit.agents import function_tool
import os
import psutil
>>>>>>> master

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
<<<<<<< HEAD
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
=======
>>>>>>> master
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
<<<<<<< HEAD
        time.sleep(0.6)
=======
        await asyncio.sleep(0.6)
>>>>>>> master
        return ack
    except Exception:
        # Fallback to known subprocess starts for common apps
        if _fallback_known_apps(norm):
            return _speak_ack(f"Opening {norm}...")
        # Final verbal failure
        return _speak_ack(f"Sorry, I couldn't find {norm} on this system.")


@function_tool()
<<<<<<< HEAD
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
=======
async def assistant_open_command(command: str) -> str:
    """
    Detects phrases like "open <app>" and triggers open_application.
>>>>>>> master
    Returns a user-facing verbal response string.
    """
    if not command:
        return ""
    text = command.strip()
    lower = text.lower()
<<<<<<< HEAD
    
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
=======
    if "open" in lower:
        # extract best-effort app name after the first occurrence of 'open'
>>>>>>> master
        try:
            idx = lower.index("open")
            candidate = text[idx + len("open"):].strip().strip('"\' ')
            if candidate:
                return await open_application(candidate)
        except Exception:
            pass
<<<<<<< HEAD
    
    return ""
=======
    return ""


@function_tool()
async def close_application(app_name: str) -> str:
    """
    Closes a Windows application using taskkill command or psutil.
    Returns a user-facing verbal response string.
    """
    if not app_name or not app_name.strip():
        return _speak_ack("Please specify an app to close.")

    norm = _normalize(app_name)
    print(f"[Assistant]: Trying to close {norm}")

    try:
        # Map common app names to their process names
        process_map = {
            "Google Chrome": "chrome.exe",
            "Microsoft Edge": "msedge.exe",
            "Calculator": "calculator.exe",
            "Notepad++": "notepad++.exe",
            "Notepad": "notepad.exe",
            "Word": "winword.exe",
            "Excel": "excel.exe",
            "PowerPoint": "powerpnt.exe",
            "Paint": "mspaint.exe",
        }
        
        # Get the process name for the app
        process_name = process_map.get(norm, norm.lower() + ".exe")
        
        # Check if the application is running first
        if not _is_application_running(process_name):
            return _speak_ack(f"Sorry, {norm} doesn't appear to be running.")
        
        # First try using taskkill command as it's more reliable on Windows
        try:
            result = subprocess.run(
                ["taskkill", "/f", "/im", process_name], 
                capture_output=True, 
                text=True, 
                shell=True
            )
            
            if result.returncode == 0:
                return _speak_ack(f"Closed {norm}.")
        except Exception:
            pass
        
        # Fallback to psutil if taskkill fails
        closed = False
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)  # Wait up to 3 seconds for graceful termination
                        closed = True
                    except psutil.TimeoutExpired:
                        # If graceful termination fails, try force kill
                        proc.kill()
                        closed = True
                    except psutil.NoSuchProcess:
                        closed = True
                    except psutil.AccessDenied:
                        # Try taskkill by PID as last resort
                        try:
                            subprocess.run(["taskkill", "/f", "/pid", str(proc.info['pid'])], 
                                         capture_output=True, shell=True)
                            closed = True
                        except:
                            pass
                    if closed:
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                continue
        
        if closed:
            return _speak_ack(f"Closed {norm}.")
        else:
            return _speak_ack(f"Sorry, I couldn't close {norm}.")
                
    except Exception as e:
        print(f"Error closing application: {e}")
        return _speak_ack(f"Sorry, I encountered an error while trying to close {norm}.")


@function_tool()
async def list_running_applications() -> str:
    """
    Lists common applications that are currently running.
    Returns a user-facing verbal response string.
    """
    try:
        # Map process names to user-friendly names
        process_map = {
            "chrome.exe": "Google Chrome",
            "msedge.exe": "Microsoft Edge",
            "notepad.exe": "Notepad",
            "notepad++.exe": "Notepad++",
            "calculator.exe": "Calculator",
            "winword.exe": "Microsoft Word",
            "excel.exe": "Microsoft Excel",
            "powerpnt.exe": "Microsoft PowerPoint",
            "mspaint.exe": "Paint",
        }
        
        running_apps = []
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in process_map:
                    friendly_name = process_map[proc_name]
                    if friendly_name not in running_apps:
                        running_apps.append(friendly_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if running_apps:
            app_list = ", ".join(running_apps)
            return f"The following applications are currently running: {app_list}."
        else:
            return "No common applications are currently running."
                
    except Exception as e:
        print(f"Error listing applications: {e}")
        return "Sorry, I encountered an error while trying to list running applications."


@function_tool()
async def assistant_list_command(command: str) -> str:
    """
    Detects phrases like "list running apps" or "what's running" and triggers list_running_applications.
    Returns a user-facing verbal response string.
    """
    if not command:
        return ""
    text = command.strip()
    lower = text.lower()
    if any(phrase in lower for phrase in ["list running", "what's running", "which apps", "running apps"]):
        return await list_running_applications()
    return ""


def _is_application_running(process_name: str) -> bool:
    """
    Check if an application with the given process name is currently running.
    """
    try:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception:
        return False


def _close_by_window_title(app_name: str) -> bool:
    """
    Attempts to close an application by finding its window and sending Alt+F4.
    Returns True if successful, False otherwise.
    """
    try:
        # Use pyautogui to find window and close it
        pyautogui.FAILSAFE = False
        
        # Try to find the window by title (this is a simplified approach)
        # In a real implementation, you might want to use a more robust window management library
        
        # For now, we'll just return False to indicate this method isn't fully implemented
        return False
    except Exception:
        return False
>>>>>>> master
