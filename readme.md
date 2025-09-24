# RamLal-X


[![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)](https://www.python.org/) 
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-brightgreen?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) 
[![LiveKit](https://img.shields.io/badge/LiveKit-Realtime-purple)](https://livekit.io/) 
[![Google Custom Search](https://img.shields.io/badge/Google%20Search-API-yellow?logo=google&logoColor=white)](https://developers.google.com/custom-search/) 
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**RamLal-X** is a personal AI assistant.  
It’s designed to support studies, coding, and personal tasks while speaking naturally in **both Hindi and English** with a proper Hindi accent for Hindi sentences.

---

## Features ✨

- **Multilingual Speech**: Speaks English and Hindi naturally.  
- **Voice Interaction**: Fully interactive via real-time voice commands.  
- **Web Search**: Uses Google Custom Search API to answer queries dynamically.  
- **Tools Integration**: Weather info, current date & time, and more.  
- **Real-time Response**: Powered by LiveKit RealtimeModel with TTS.  
- **Interruptible Speech**: Say "Jarvis wait" to interrupt ongoing speech (feature in progress).  
- **Proactive Introduction**: Automatically introduces itself when started.  
- **Witty & Loyal Persona**: Modeled after “RamLal” — intelligent, witty, and helpful.

---
## Installation 💻

1. Clone the repository:

```bash
git clone https://github.com/abhinavsaxena2308/RamLal-X.git
cd RamLal-X
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Add your API keys in a .env file:

```bash
LIVEKIT_API_KEY= <your_key>
LIVEKIT_API_SECRET= <your_key>
GOOGLE_API_KEY = <your_key>
GOOGLE_SEARCH_API_KEY= <your_key>
SEARCH_ENGINE_ID = <your_key>
```
---
## Running the Assistant 🚀
Console Version
```bash
python agent.py
```
---
## Technologies Used

- **Python 3.13+**  
- **LiveKit Agents & RealtimeModel** for real-time AI voice assistant capabilities  
- **Google Custom Search API** for dynamic web search  
- **dotenv** for managing API keys and environment variables  
- **asyncio** for asynchronous operations and smooth TTS interactions  

---

## License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute it with proper attribution.

---

## Author

**Abhinav Utkarsh Pankaj** – Creator of RamLal-X  
Inspired by Jarvis, this assistant is designed for bilingual Hindi-English interaction, study help, coding support, and personal tasks.
