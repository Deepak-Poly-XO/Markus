import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav
import webrtcvad
import torch
import warnings
import os
import pyaudio

warnings.filterwarnings("ignore")

# ── DEVICE SELECTION ───────────────────────────────────
HEADSET_MIC = 1  # WH-CH720N
LAPTOP_MIC  = 2  # Microphone Array (Realtek)

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

# ── WHISPER MODEL ──────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
model  = whisper.load_model("base", device=device)
vad    = webrtcvad.Vad(2)

SAMPLE_RATE   = 16000
FRAME_MS      = 30
FRAME_SIZE    = int(SAMPLE_RATE * FRAME_MS / 1000)
MIN_SPEECH    = 0.5

def listen(silence_limit=0.8, sample_rate=16000):
    print("🎙️  Listening...")

    speech_frames = []
    silent_chunks = 0
    speaking      = False

    max_silent = int(silence_limit * 1000 / FRAME_MS)
    min_speech = int(MIN_SPEECH * 1000 / FRAME_MS)

    input_device = get_input_device()

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype='int16',
            blocksize=FRAME_SIZE,
            device=input_device
        ) as stream:
            while True:
                frame, _    = stream.read(FRAME_SIZE)
                frame_bytes = frame.tobytes()

                energy = np.abs(frame.astype(np.float32)).mean()
                if energy < 200:
                    if speaking:
                        silent_chunks += 1
                        if silent_chunks > max_silent:
                            print("🔇  Speech ended.")
                            break
                    continue

                is_speech = vad.is_speech(frame_bytes, sample_rate)

                if is_speech:
                    speaking      = True
                    silent_chunks = 0
                    speech_frames.append(frame.copy())
                else:
                    if speaking:
                        silent_chunks += 1
                        speech_frames.append(frame.copy())
                        if silent_chunks > max_silent:
                            print("🔇  Speech ended.")
                            break
                    else:
                        silent_chunks += 1
                        if silent_chunks > max_silent:
                            print("🔇  No speech detected.")
                            return ""

    except Exception as e:
        print(f"❌ Listener error: {e}")
        return ""

    if len(speech_frames) < min_speech:
        return ""

    print("🔄  Processing...")
    audio_np = np.concatenate(speech_frames).flatten().astype(np.float32) / 32768.0

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
        wav.write(temp_path, sample_rate, (audio_np * 32767).astype(np.int16))

    result = model.transcribe(
        temp_path,
        initial_prompt="MARKUS open close volume screenshot notepad Spotify Chrome",
        language="en"
    )
    os.remove(temp_path)

    text = result["text"].strip()
    print(f"📝  You said: {text}")
    return text