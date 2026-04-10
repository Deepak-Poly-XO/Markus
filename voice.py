import edge_tts
import asyncio
import subprocess
import re

async def _speak_async(text):
    communicate = edge_tts.Communicate(
        text,
        voice="en-GB-RyanNeural",
        rate="+5%",
        volume="+0%",
        pitch="-15Hz"
    )
    process = subprocess.Popen(
        ['ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            process.stdin.write(chunk["data"])
    process.stdin.close()
    process.wait()

def clean_text(text):
    text = re.sub(r'\*+', '', text)        # remove ** and *
    text = re.sub(r'#+\s', '', text)       # remove ## headers
    text = re.sub(r'`+', '', text)         # remove code backticks
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # links
    return text.strip()

def speak(text):
    # Import here to avoid circular import
    from wakeword import speaking_event
    text = clean_text(text)
    print(f"🤖 MARKUS: {text}")
    speaking_event.set()          # ← Block wake word detection
    asyncio.run(_speak_async(text))
    speaking_event.clear()        # ← Resume after speaking done