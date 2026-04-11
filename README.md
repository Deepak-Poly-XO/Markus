# MARKUS — Personal AI System

> *"Advanced AI assistant built from scratch. Inspired by Jarvis. Powered by Claude."*

Built by **Deepu** — Calgary, AB

---

## What Is MARKUS?

MARKUS is a fully voice-controlled personal AI assistant that runs locally on your PC. It listens for your wake word, understands natural language, controls your computer, fetches real-time information, and remembers you across sessions.

---

## Features

**Voice Interaction**
- Custom wake word detection — say "MARKUS" to activate
- Voice Activity Detection — stops listening when you stop talking
- Whisper-powered speech recognition running on GPU
- Natural text-to-speech with Microsoft Neural voices

**AI Brain**
- Powered by Claude (Anthropic)
- Full conversation memory within sessions
- Persistent memory across sessions via JSON storage
- Remembers facts, keywords, and preferences you tell it

**PC Control**
- Opens any installed app by voice
- Closes running apps
- Opens websites in browser
- Opens apps and writes content inside them
- Takes screenshots saved to Desktop
- Controls system volume
- Reads battery, CPU, and RAM stats

**Real-Time Information**
- Live weather for any city via OpenWeatherMap API
- Web search powered by DDGS
- Smart query building — Claude constructs the search query

**UI**
- Cinematic dark HUD interface built with PyWebView + HTML/CSS/JS
- Animated central orb with spinning rings and pulse effect
- Live conversation log, system log, and notifications
- Real-time CPU, RAM, and battery progress bars
- Audio waveform visualizer
- Fullscreen toggle with F11

---

## Tech Stack

| Component | Technology |
|---|---|
| Wake Word | OpenAI Whisper (tiny model) |
| Speech to Text | OpenAI Whisper (base model) |
| AI Brain | Anthropic Claude API |
| Text to Speech | Edge-TTS (Microsoft Neural) |
| PC Control | pyautogui, pygetwindow, psutil |
| Web Search | DDGS |
| Weather | OpenWeatherMap API |
| UI | PyWebView + HTML/CSS/JS |
| Memory | JSON flat file |

---

## Project Structure

```
markus/
├── main.py          # Entry point, wake word loop, shutdown
├── brain.py         # Claude API, command parsing, memory integration
├── listener.py      # Microphone input, VAD, Whisper transcription
├── voice.py         # Text-to-speech via edge-tts + ffplay
├── wakeword.py      # Whisper-based wake word detection
├── controller.py    # PC control — apps, browser, volume, screenshots
├── search.py        # Web search via DDGS
├── weather.py       # Real-time weather via OpenWeatherMap
├── memory.py        # Persistent JSON memory system
├── ui.py            # PyWebView window manager
├── markus_ui.html   # Full HUD interface
├── config.py        # API keys and MARKUS persona (gitignored)
└── memory.json      # Persistent memory store (gitignored)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Deepak-Poly-XO/Markus.git
cd Markus
```

### 2. Install dependencies

```bash
pip install anthropic openai-whisper edge-tts sounddevice scipy numpy \
            keyboard pygame psutil pyautogui pygetwindow pywebview \
            ddgs requests pyperclip pillow webrtcvad torch
```

### 3. Install ffmpeg

```bash
winget install ffmpeg
```

### 4. Create `config.py`

```python
API_KEY = "your-anthropic-api-key"

MARKUS_PERSONA = """
You are MARKUS, an advanced AI personal assistant.
Your user's name is Deepu. You are based in Calgary.
You are intelligent, efficient, slightly witty, and always professional.
Speak naturally — you are having a voice conversation, not writing.
Never use markdown, bullet points, or JSON in responses.
"""
```

### 5. Create `weather.py`

```python
import requests

API_KEY = "your-openweathermap-api-key"

def get_weather(city="Calgary"):
    try:
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city, "appid": API_KEY, "units": "metric", "cnt": 8}
        res = requests.get(url, params=params).json()
        if str(res.get("cod")) in ["401", "404"]:
            return None
        out = f"Weather in {city}:\n"
        for item in res["list"]:
            out += f"{item['dt_txt']} → {item['main']['temp']}°C, {item['weather'][0]['description']}\n"
        return out
    except:
        return None
```

### 6. Run MARKUS

```bash
python main.py
```

---

## Usage

| Action | How |
|---|---|
| Activate MARKUS | Say **"MARKUS"** |
| Ask anything | Speak naturally after activation |
| Open an app | "Open Spotify" |
| Open a website | "Go to YouTube" |
| Write in Notepad | "Open Notepad and write about AI" |
| Check weather | "What's the weather in Calgary?" |
| Search the web | "What's the latest news on AI?" |
| Take screenshot | "Take a screenshot" |
| Volume control | "Turn the volume up" |
| System stats | "What's my battery level?" |
| Save a fact | "Remember my keyword is rocket" |
| Delete a fact | "Forget the keyword" |
| Toggle fullscreen | Press **F11** |
| Shutdown MARKUS | Press **Escape** |

---

## API Keys Required

- **Anthropic API** → [console.anthropic.com](https://console.anthropic.com)
- **OpenWeatherMap API** → [openweathermap.org](https://openweathermap.org/api) — free tier

---

## Roadmap

- Spotify song control via Spotify Web API
- Email and calendar integration
- Screen reading and vision capabilities
- Wake word trained on personal voice samples
- Mobile companion app

---

## Notes

- `config.py` and `weather.py` are gitignored — never commit API keys
- `memory.json` is gitignored — your personal data stays local
- First run downloads Whisper model files (~150MB)
- App cache builds on startup (~5 seconds) then instant thereafter

---

*MARKUS — Built in Calgary. One session at a time.*
