import pyaudio
import numpy as np
import whisper
import torch
import threading
import time

# Reuse existing whisper model
wake_model = whisper.load_model("tiny")  # tiny = fast, just for wake word
speaking_event = threading.Event()

def listen_for_wakeword(callback):
    pa         = pyaudio.PyAudio()
    CHUNK      = 16000  # 1 second
    RATE       = 16000

    stream = pa.open(
        rate=RATE,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("👂 Listening for 'MARKUS'...")

    while True:
        try:
            if speaking_event.is_set():
                if stream.is_active():
                    stream.stop_stream()
                time.sleep(0.1)
                continue

            if not stream.is_active():
                time.sleep(0.5)
                stream = pa.open(
                    rate=RATE, channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=CHUNK
                )
                continue

            audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
            audio_np    = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

            # Only run Whisper if audio is loud enough
            energy = np.abs(audio_np).mean()
            if energy < 0.01:  # silence threshold
                continue

            # Run Whisper on chunk
            result = wake_model.transcribe(
                audio_np,
                language="en",
                fp16=False
            )
            text = result["text"].strip().lower()
            print(f"👂 Heard: {text}")

            # Check for wake word variations
            wake_words = ["markus", "marcus", "mark us", "marquis"]
            if any(w in text for w in wake_words):
                print(f"✅ MARKUS detected!")
                stream.stop_stream()
                callback()
                time.sleep(2)
                stream.start_stream()

        except OSError:
            try: stream.close()
            except: pass
            time.sleep(1.0)
            stream = pa.open(
                rate=RATE, channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=CHUNK
            )
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(0.5)