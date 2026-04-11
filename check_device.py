# find_mic.py — test ALL devices
import pyaudio
pa = pyaudio.PyAudio()

print("\n🎙️ ALL active input devices:\n")
for idx in range(pa.get_device_count()):
    try:
        info = pa.get_device_info_by_index(idx)
        if info['maxInputChannels'] < 1:
            continue
        test = pa.open(
            rate=16000, channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=idx,
            frames_per_buffer=1024
        )
        test.close()
        print(f"✅ [{idx}] ACTIVE: {info['name']}")
    except Exception as e:
        print(f"❌ [{idx}] Dead:   {info['name'][:40]}")

pa.terminate()