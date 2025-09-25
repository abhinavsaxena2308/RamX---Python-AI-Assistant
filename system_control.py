import os
import subprocess
import psutil
import logging
from livekit.agents import function_tool, RunContext

@function_tool()
async def system_controls(ctx: RunContext, command: str, target: str = None) -> str:
    """
    Control system with natural commands:
    - shutdown / restart / sleep
    - open app by name
    - close app by name
    - play mp3/mp4 files
    - list folder items
    - create new folder
    - check battery percentage
    - open settings / system info
    """

    try:
        cmd = command.lower()

        # 🔹 Shutdown
        if cmd == "shutdown":
            subprocess.run("shutdown /s /t 1", shell=True)
            return "System shutting down..."

        # 🔹 Restart
        elif cmd == "restart":
            subprocess.run("shutdown /r /t 1", shell=True)
            return "System restarting..."

        # 🔹 Sleep
        elif cmd == "sleep":
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return "System going to sleep..."

        # 🔹 Open App
        elif cmd == "open app" and target:
            try:
                subprocess.Popen(target, shell=True)
                return f"Opening {target}..."
            except FileNotFoundError:
                return f"{target} not found on this system."

        # 🔹 Close App
        elif cmd == "close app" and target:
            for proc in psutil.process_iter(['pid', 'name']):
                if target.lower() in proc.info['name'].lower():
                    proc.kill()
                    return f"Closed {target}."
            return f"{target} was not running."

        # 🔹 Play Media
        elif cmd == "play media" and target:
            if os.path.exists(target):
                subprocess.Popen(["start", target], shell=True)
                return f"Playing {os.path.basename(target)}..."
            else:
                return "File not found."

        # 🔹 List Folder Items
        elif cmd == "list folder" and target:
            if os.path.isdir(target):
                items = os.listdir(target)
                return f"Items in {target}:\n" + "\n".join(items)
            else:
                return "Invalid folder path."

        # 🔹 Create New Folder
        elif cmd == "new folder" and target:
            os.makedirs(target, exist_ok=True)
            return f"Folder created at {target}."

        # 🔹 Battery Percentage
        elif cmd == "battery":
            battery = psutil.sensors_battery()
            if battery:
                return f"Battery at {battery.percent}%"
            return "Battery status not available."

        # 🔹 Open Settings
        elif cmd == "settings":
            subprocess.Popen("start ms-settings:", shell=True)
            return "Opening Settings..."

        # 🔹 System Info
        elif cmd == "system info":
            subprocess.Popen("msinfo32", shell=True)
            return "Opening System Information..."

        else:
            return "Invalid or incomplete command."

    except Exception as e:
        logging.error(f"System control error: {e}")
        return f"Error: {e}"
