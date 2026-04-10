import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
import time

SAMPLE_RATE = 16000
DURATION    = 2  # seconds per recording
SAMPLES_DIR = "wakeword_samples"
os.makedirs(SAMPLES_DIR, exist_ok=True)

def record_sample(index):
    print(f"\n🎙️  Recording sample {index+1}/30...")
    print("Say 'MARKUS' clearly in 3 seconds...")
    time.sleep(1)
    print("GO!")
    
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16'
    )
    sd.wait()
    
    path = os.path.join(SAMPLES_DIR, f"markus_{index:03d}.wav")
    wav.write(path, SAMPLE_RATE, audio)
    print(f"✅ Saved: {path}")

print("=== MARKUS Wake Word Recorder ===")
print("We need 30 samples of you saying 'MARKUS'")
print("Say it naturally — different tones, speeds, distances")
input("\nPress Enter to start...")

for i in range(30):
    record_sample(i)
    if i < 29:
        time.sleep(0.5)

print("\n✅ All 30 samples recorded!")
print(f"📁 Saved in: {SAMPLES_DIR}/")