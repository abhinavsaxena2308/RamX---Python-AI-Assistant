import sqlite3
import subprocess
import os
from typing import Optional
from functools import wraps
from livekit.agents import function_tool

DB_PATH = "Ramx.db"  
TOOLS = {}  

def tool(name: str):
    """
    Decorator to register a function as a callable tool.
    """
    def decorator(fn):
        TOOLS[name] = fn
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_app_path(app_name: str) -> Optional[str]:
    """
    Fetch the app path from the database.
    Searches both sys_command and web_command tables.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

   
    cursor.execute("SELECT path FROM sys_command WHERE name = ?", (app_name,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]

    cursor.execute("SELECT path FROM web_command WHERE name = ?", (app_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]

    return None


@function_tool()
def open_app(app_name: str) -> str:
    """
    Opens the app using the path in RamX.db.
    Returns a status message.
    """
    path = get_app_path(app_name)
    if not path:
        return f"[ERROR] App '{app_name}' not found in database."

    # If the stored path is a URL (from web_command), open in default browser
    if path.lower().startswith(("http://", "https://")):
        try:
            import webbrowser
            webbrowser.open(path)
            return f"[INFO] Opening '{app_name}' in browser: {path}"
        except Exception as e:
            return f"[ERROR] Failed to open URL '{path}': {e}"

    # Otherwise treat as local application path (from sys_command)
    if not os.path.exists(path):
        return f"[ERROR] Path '{path}' does not exist."

    try:
        subprocess.Popen(path, shell=True)
        return f"[INFO] Opening '{app_name}'..."
    except Exception as e:
        return f"[ERROR] Failed to open '{app_name}': {e}"

@function_tool
async def assistant_command_listener(command: str) -> str:
    """
    Parses the user command and calls the appropriate tool.
    e.g., "open Chrome" -> calls open_app("Chrome")
    """
    command = command.strip().lower()
    if command.startswith("open "):
        # Extract app name
        app_name = command.replace("open ", "").strip()
        if "open_app" in TOOLS:
            return await TOOLS["open_app"](app_name)
        else:
            return "[ERROR] No tool registered to open apps."
    else:
        return "[INFO] Command not recognized."


if __name__ == "__main__":
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting assistant...")
            break
        response = assistant_command_listener(user_input)
        print(response)
