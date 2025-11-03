import json
import socket
from typing import Literal
from livekit.agents import function_tool

_ADDR = ("127.0.0.1", 8765)


def _normalize(expr: str) -> str:
    e = expr.strip().lower()
    # Map common phrases to canonical expressions used by desktop_avatar.py
    if any(k in e for k in ["wink", "winking", "😉", "winky"]):
        return "wink"
    if any(k in e for k in ["smile open", "open mouth smile", "big smile", "😀", "😃", "open smile"]):
        return "smile_open"
    if any(k in e for k in ["cool", "sunglasses", "😎", "shades"]):
        return "cool"
    if any(k in e for k in ["happy", "joy", "joyful", "😊", "😄", "excited", "tears of joy", "awesome"]):
        return "happy"
    if any(k in e for k in ["sad", "crying", "😢", "😭", "unhappy", "down"]):
        return "sad"
    if any(k in e for k in ["surprised", "shock", "😲", "😮", "amazed", "wow"]):
        return "surprised"
    if any(k in e for k in ["angry", "mad", "😠", "😡", "furious", "annoyed"]):
        return "angry"
    if any(k in e for k in ["sleepy", "tired", "😴", "yawn", "drowsy"]):
        return "sleepy"
    if any(k in e for k in ["thinking", "hmm", "🤔", "pondering", "wondering"]):
        return "thinking"
    if any(k in e for k in ["love", "heart", "😍", "❤️", "💕", "adore"]):
        return "love"
    if e in {"neutral", "reset", "rest"}:
        return "neutral"
    # Fallback: pass through if it matches known ones
    if e in {"wink", "smile_open", "neutral", "cool", "happy", "sad", "surprised", "angry", "sleepy", "thinking", "love"}:
        return e
    return "neutral"


@function_tool()
async def set_avatar_expression(expr: str, duration: float = 1.2) -> str:
    """
    Show an expression on the desktop avatar (PySide6 window).
    Expressions: wink, smile_open, cool, happy, sad, surprised, angry, sleepy, thinking, love, neutral
    The avatar app must be running: python -m avatar.desktop_avatar
    """
    canon = _normalize(expr)
    payload = json.dumps({"expr": canon, "duration": float(duration)}).encode("utf-8")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(payload, _ADDR)
    except Exception as e:
        return f"failed: {e}"
    return f"ok: {canon} for {duration:.2f}s"
