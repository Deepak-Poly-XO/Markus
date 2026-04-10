import edge_tts
import asyncio
import subprocess

async def _speak_async(text):
    communicate = edge_tts.Communicate(
        text,
        voice="en-GB-RyanNeural",
        rate="+5%",
        volume="+0%",
        pitch="-10Hz"
    )

    # ffplay starts playing the moment first chunk arrives
    process = subprocess.Popen(
        ['ffplay', '-nodisp', '-autoexit', '-i', 'pipe:0'],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            process.stdin.write(chunk["data"])  # feed chunks as they arrive

    process.stdin.close()
    process.wait()

def speak(text):
    print(f"🤖 MARKUS: {text}")
    asyncio.run(_speak_async(text))