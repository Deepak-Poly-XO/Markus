import pyaudio
import numpy as np
import whisper
import torch
import threading
import time

wake_model     = whisper.load_model("tiny")
speaking_event = threading.Event()

def listen_for_wakeword(callback):
    CHUNK = 16000
    RATE  = 16000

    pa = pyaudio.PyAudio()

    def get_input_device():
        pa = pyaudio.PyAudio()
        best_device = None

        for i in range(pa.get_device_count()):
            try:
                info = pa.get_device_info_by_index(i)
                if info['maxInputChannels'] < 1:
                    continue
                name = info['name'].lower()

                # Test if device actually opens
                test = pa.open(
                    rate=16000, channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=1024
                )
                test.close()

                # Prefer Bluetooth headset
                if any(x in name for x in ["wh-ch", "headset", "bluetooth", "rockerz", "airdopes", "soundpeats", "pulse5"]):
                    pa.terminate()
                    print(f"🎧 Using headset: {info['name'][:35]}")
                    return i

                # Save Realtek as fallback
                if "realtek" in name and "microphone array" in name and best_device is None:
                    best_device = i

            except:
                continue

        pa.terminate()
        if best_device is not None:
            print(f"🎙️ Using laptop mic: Microphone Array (Realtek)")
            return best_device

        print("🎙️ Using default device")
        return None  # sounddevice will use system default

    def make_stream():
        device = get_input_device()
        return pa.open(
            rate=RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=device,
            frames_per_buffer=CHUNK
        )

    def reinit():
        nonlocal pa
        try: pa.terminate()
        except: pass
        pa = pyaudio.PyAudio()
        return make_stream()

    stream = make_stream()
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
                stream = reinit()
                print("👂 Wake word ready...")
                continue

            audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
            audio_np    = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

            energy = np.abs(audio_np).mean()
            if energy < 0.01:
                continue

            result = wake_model.transcribe(
                audio_np,
                language="en",
                fp16=False,
                initial_prompt="MARKUS open close volume screenshot notepad Spotify Chrome"
            )
            text = result["text"].strip().lower()

            if text:
                print(f"👂 Heard: {text}")

            wake_words = ["markus", "marcus", "mark us", "marquis"]
            if any(w in text for w in wake_words):
                print(f"✅ MARKUS detected!")
                stream.stop_stream()
                callback()
                time.sleep(2)
                stream = reinit()
                print("👂 Listening for 'MARKUS'...")

        except OSError:
            print("🔄 Audio device changed — reconnecting...")
            try: stream.close()
            except: pass
            time.sleep(1.5)
            try:
                stream = reinit()
                print("👂 Reconnected — wake word ready...")
            except Exception as e:
                print(f"❌ Audio reinit failed: {e}")
                time.sleep(2)

        except Exception as e:
            print(f"❌ Wake word error: {e}")
            time.sleep(0.5)