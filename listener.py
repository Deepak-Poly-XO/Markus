import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav
import webrtcvad
import torch
import warnings
import collections
import os

warnings.filterwarnings("ignore")

device = "cuda" if torch.cuda.is_available() else "cpu"
model  = whisper.load_model("base", device=device)
vad    = webrtcvad.Vad(2)  # 0=least aggressive, 3=most aggressive

SAMPLE_RATE    = 16000
FRAME_MS       = 30          # webrtcvad needs 10, 20 or 30ms frames
FRAME_SIZE     = int(SAMPLE_RATE * FRAME_MS / 1000)  # 480 samples
SILENCE_LIMIT  = 1.5         # seconds of silence before stopping
MIN_SPEECH     = 0.5         # minimum seconds of speech to process

def listen(silence_limit=0.8, sample_rate=16000):
    print("🎙️  Listening...")

    speech_frames = []
    silent_chunks = 0
    speaking      = False

    max_silent = int(silence_limit * 1000 / FRAME_MS)
    min_speech = int(MIN_SPEECH * 1000 / FRAME_MS)

    with sd.InputStream(samplerate=sample_rate, channels=1,
                        dtype='int16', blocksize=FRAME_SIZE) as stream:
        while True:
            frame, _    = stream.read(FRAME_SIZE)
            frame_bytes = frame.tobytes()

            # ← Check energy before VAD
            energy = np.abs(frame.astype(np.float32)).mean()
            if energy < 200:  # too quiet — ignore completely
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
        initial_prompt="MARKUS open Notepad Spotify Chrome VS Code close volume screenshot write",
        language="en"
    )
    os.remove(temp_path)

    text = result["text"].strip()
    print(f"📝  You said: {text}")
    return text