# Installing packages on Raspberry Pi 4 for sound recognition and clap detection
sudo apt update
sudo apt install python3-pyaudio
arecord -l

import pyaudio
import numpy as np
import time
import os

# ===== Parameters =====
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 2500  # Volume threshold
MICROPHONE_INDEX = 1

# Recognition parameters
DOUBLE_CLAP_TIMEOUT = 1.0   # Maximum time between claps (sec)
MIN_CLAP_INTERVAL = 0.2     # Minimum time between claps (sec)
COOLDOWN = 1.5              # Delay between clap sequences

# ===== State =====
light_on = False
last_clap_time = 0
clap_times = []

print("🔊 Double Clap Detector")
print("=" * 60)
print("💡 Light is OFF")
print("Double clap to toggle light")
print("Press Ctrl+C to stop")
print("=" * 60)

# ===== Initialization =====
p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    input_device_index=MICROPHONE_INDEX,
    frames_per_buffer=CHUNK
)

def is_clap(audio_data):
    """Check if sound is a clap"""
    volume = np.max(np.abs(audio_data))
    return volume > THRESHOLD, volume

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        current_time = time.time()

        detected, volume = is_clap(audio_data)
        if detected:
            time_since_last = current_time - last_clap_time
            last_clap_time = current_time

            if time_since_last > MIN_CLAP_INTERVAL:
                clap_times.append(current_time)
                print(f"👏 Clap detected! Volume: {volume}")

                # Check for 2 consecutive claps
                if len(clap_times) >= 2:
                    interval = clap_times[-1] - clap_times[-2]
                    if interval <= DOUBLE_CLAP_TIMEOUT:
                        light_on = not light_on
                        os.system('cls' if os.name == 'nt' else 'clear')
                        print("🔊 Double Clap Detector")
                        print("=" * 60)
                        print(f"💡 Light is {'ON' if light_on else 'OFF'}")
                        print("=" * 60)
                        clap_times = []  # reset
                    else:
                        # If interval is too long - start over
                        clap_times = [clap_times[-1]]

        # Timeout reset
        if clap_times and (current_time - clap_times[-1]) > COOLDOWN:
            clap_times = []

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n🛑 Program stopped by user")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
