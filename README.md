# FRIDAY — Personal AI Assistant

A voice-activated personal AI assistant inspired by Iron Man's FRIDAY.
Built entirely in Python with a modular skill-based architecture.

## Features
- Wake word detection — "Hey FRIDAY"
- Natural voice conversations powered by Groq LLaMA 3.3
- Live web-aware answers via DuckDuckGo search
- Weather, news, reminders, alarms
- Music playback via YouTube streaming
- App and website launcher
- Long-term memory across sessions
- Morning briefing
- Desktop UI with system tray
- Modular skill system — easily extensible

## Tech Stack
- Python 3.12
- Groq API (LLaMA 3.3 70B)
- Edge TTS + PyAudio + SpeechRecognition
- PyQt6 (UI)
- yt-dlp + python-vlc (music)
- DuckDuckGo Search
- OpenWeatherMap API

## Architecture
FRIDAY uses a layered processing pipeline:
1. Wake word detection (passive listening)
2. Speech to text transcription
3. Personality handler (conversational responses)
4. Skill router (matches intent to skill)
5. Brain fallback (Groq LLaMA for general queries)
6. Text to speech response

## Setup
1. Clone the repo
2. Create virtual environment and install dependencies
3. Add your API keys to .env
4. Run python main.py

## Skills
| Skill | Trigger phrases |
|---|---|
| Weather | "what's the weather" |
| News | "latest news", "cricket news" |
| Music | "play Kesariya" |
| Calculator | "what is 15% of 5000" |
| Reminders | "remind me in 5 minutes to..." |
| App launcher | "open VS Code" |
| Website opener | "open YouTube" |
| Morning briefing | "good morning" |
| System control | "take a screenshot", "mute" |
