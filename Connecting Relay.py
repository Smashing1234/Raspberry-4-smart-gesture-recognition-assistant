# Install ESP version 13.04.0 via Tasmotizer, then in Tasmotizer set up MQTT broker with Raspberry Pi IP
# Important: ESP and Raspberry Pi must be connected to same Wi-Fi (I used phone hotspot)
# Also set Host and Wi-Fi password
# Then we get ESP IP address. Enter it in browser to access ESP web interface

# Connection diagram:
"""
RELAY Module:

VCC  ← 3.3V (ESP)
GND  ← GND (ESP)
IN   ← D3 (ESP)

COM  → 3.3V (ESP)
NO   → LED Anode (+)
NC   → (NOT USED)

LED Connection:
Anode (+) ← Relay NO
Cathode (-) → 220Ω → GND (ESP)
"""

# In web interface:
# "Configuration" → "Configure Module" → "Module Type" → Generic (18)
# Save and wait for reboot
# Then: "Configuration" → "Configure Module" → D3 GPIO0 → Relay_i (1)
# Save and wait for reboot
# Test relay with toggle switch on main page - should click and control light

# MQTT connection with Raspberry Pi 4 was covered in previous article

# Complete working code

import cv2
import mediapipe as mp
import time
import requests
import paho.mqtt.client as mqtt
import pyaudio
import numpy as np
import os
import threading

# ===== Settings =====
TELEGRAM_BOT_TOKEN = "7125494325:AAEOSMBbpjZgqoIArsCex3hblWWsNFjOyiE"
TELEGRAM_CHAT_ID = "1880548453"

# ===== MQTT Settings =====
MQTT_BROKER = "172.20.10.2"  # Raspberry Pi IP
MQTT_PORT = 1883
MQTT_TOPIC = "cmnd/tasmota_DEE65D/POWER"
MQTT_USER = "DVES_USER"
MQTT_PASS = "147"

# ===== Audio Parameters =====
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 2500  # Volume threshold

# Clap parameters with 1-1.5 second conditions
DOUBLE_CLAP_MIN_TIMEOUT = 1.0   # Minimum time between claps
DOUBLE_CLAP_MAX_TIMEOUT = 1.5   # Maximum time between claps
MIN_CLAP_INTERVAL = 0.1         # Minimum time between claps
COOLDOWN = 2.0                  # Timer reset time

# ===== Variables =====
last_call_time = 0
call_cooldown = 300
hold_time_needed = 2
max_distance = 24

# ===== Global variables for claps =====
clap_times = []
lights_on = False
last_light_time = 0
light_cooldown = 1.0
clap_timeout_timer = 0  # Timer for clap reset

# ===== Initialization =====
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Try to initialize camera
try:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not available")
        cap = None
    else:
        print("✅ Camera initialized")
except:
    print("❌ Camera initialization failed")
    cap = None

# ===== MQTT Client =====
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# ===== Audio Initialization =====
p = None
stream = None
try:
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=1
    )
    print("✅ Microphone initialized")
except Exception as e:
    print(f"❌ Microphone initialization failed: {e}")
    p = None
    stream = None

# Gesture detection state
gesture_start_time = 0
gesture_detected = False
fist_start_time = 0
fist_detected = False

def connect_mqtt():
    """Connect to MQTT broker"""
    try:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("✅ Connected to MQTT broker")
        return True
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")
        return False

def control_light(state):
    """Control light on ESP8266"""
    global lights_on
    command = "ON" if state else "OFF"
    try:
        mqtt_client.publish(MQTT_TOPIC, command)
        lights_on = state
        print(f"💡 Light: {command}")
        return True
    except Exception as e:
        print(f"❌ Command sending error: {e}")
        return False

def send_emergency():
    """Send emergency message to Telegram"""
    global last_call_time
    current_time = time.time()

    if current_time - last_call_time < call_cooldown:
        print("⏳ Emergency call on cooldown")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': "🚨 EMERGENCY CALL 🚨\n\nUser needs help!"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            last_call_time = current_time
            print("✅ Emergency call sent!")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False

def is_finger_extended(pip, dip, tip):
    """Check if finger is extended (tip above joints)"""
    return tip[1] < pip[1] and tip[1] < dip[1]

def detect_gesture(landmarks, h, w):
    """Detect fist or palm"""
    lm = [(int(p.x * w), int(p.y * h)) for p in landmarks.landmark]

    fingers = []
    # Thumb
    fingers.append(1 if lm[4][0] > lm[3][0] else 0)
    # Other 4 fingers
    for tip in [8, 12, 16, 20]:
        fingers.append(1 if lm[tip][1] < lm[tip - 2][1] else 0)

    if sum(fingers) == 0:
        return "fist"
    elif sum(fingers) == 5:
        return "palm"
    else:
        return "other"

def is_clap(audio_data):
    """Check if sound is a clap"""
    volume = np.max(np.abs(audio_data))
    return volume > THRESHOLD, volume

def process_audio_fast():
    """Fast audio processing for claps with 1-1.5 second conditions"""
    global clap_times, lights_on, last_light_time, clap_timeout_timer
    
    if stream is None:
        return
        
    try:
        # Fast data reading
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        current_time = time.time()

        detected, volume = is_clap(audio_data)
        
        if detected and volume > THRESHOLD:
            print(f"👏 Clap! Volume: {volume}")
            
            # Add clap time
            clap_times.append(current_time)
            
            # Keep only last 2 claps
            if len(clap_times) > 2:
                clap_times = clap_times[-2:]
            
            # Start reset timer
            clap_timeout_timer = current_time
            
            # Check two claps
            if len(clap_times) == 2:
                interval = clap_times[1] - clap_times[0]
                print(f"📊 Interval between claps: {interval:.3f}s")
                
                # Check condition: interval from 1 to 1.5 seconds
                if DOUBLE_CLAP_MIN_TIMEOUT <= interval <= DOUBLE_CLAP_MAX_TIMEOUT:
                    # Toggle light if enough time passed
                    if current_time - last_light_time > light_cooldown:
                        lights_on = not lights_on
                        last_light_time = current_time
                        control_light(lights_on)
                        print(f"💡 Light toggled via clap: {'ON' if lights_on else 'OFF'}")
                        # Clear array after successful toggle
                        clap_times = []
                        clap_timeout_timer = 0
                else:
                    print(f"❌ Invalid interval: {interval:.3f}s (need 1.0-1.5s)")
                    # If interval doesn't match, keep only last clap
                    clap_times = [clap_times[1]]

        # Reset timer if more than COOLDOWN seconds passed
        if clap_timeout_timer > 0 and (current_time - clap_timeout_timer) > COOLDOWN:
            print("🔄 Clap timer reset - waiting for new claps")
            clap_times = []
            clap_timeout_timer = 0

    except Exception as e:
        print(f"❌ Audio processing error: {e}")

# ===== Connect MQTT =====
if not connect_mqtt():
    print("⚠ Working without MQTT (simulation only)")

# ===== Main Loop =====
print("\n🚀 System started!")
print("Gestures:")
print("  - Fist: turn light on/off")
print("  - OK (hold 2 sec): emergency call")
print("Claps:")
print("  - Double clap (1.0-1.5s interval): turn light on/off")
print("Press 'Q' to quit\n")

try:
    while True:
        # Fast audio processing in main loop
        process_audio_fast()
        
        if cap is None:
            print("❌ Camera not available, waiting...")
            time.sleep(0.1)
            continue

        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        current_ok_gesture = False
        current_fist_gesture = False
        current_gesture = "none"

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Get finger points
                landmarks = []
                for point in hand_landmarks.landmark:
                    x = int(point.x * w)
                    y = int(point.y * h)
                    landmarks.append((x, y))

                # All finger points
                thumb_tip = landmarks[4]
                index_tip = landmarks[8]
                middle_tip = landmarks[12]
                ring_tip = landmarks[16]
                pinky_tip = landmarks[20]

                # Finger joints for extension check
                index_pip = landmarks[6]
                index_dip = landmarks[7]
                middle_pip = landmarks[10]
                middle_dip = landmarks[11]
                ring_pip = landmarks[14]
                ring_dip = landmarks[15]
                pinky_pip = landmarks[18]
                pinky_dip = landmarks[19]

                # Calculate distance between thumb and index finger
                dx = thumb_tip[0] - index_tip[0]
                dy = thumb_tip[1] - index_tip[1]
                distance = (dx * dx + dy * dy) ** 0.5

                # Check if other fingers are extended
                middle_extended = is_finger_extended(middle_pip, middle_dip, middle_tip)
                ring_extended = is_finger_extended(ring_pip, ring_dip, ring_tip)
                pinky_extended = is_finger_extended(pinky_pip, pinky_dip, pinky_tip)

                # OK gesture: thumb and index connected, other fingers extended
                if (distance < max_distance and
                        middle_extended and
                        ring_extended and
                        pinky_extended):
                    current_ok_gesture = True

                # Detect gesture using new function
                current_gesture = detect_gesture(hand_landmarks, h, w)
                if current_gesture == "fist":
                    current_fist_gesture = True

        # OK gesture processing
        current_time = time.time()

        if current_ok_gesture:
            if not gesture_detected:
                gesture_detected = True
                gesture_start_time = current_time
                print("👌 OK gesture detected...")

            # Calculate remaining time
            hold_time = current_time - gesture_start_time
            time_left = hold_time_needed - hold_time

            if time_left > 0:
                # Show countdown BELOW - to avoid overlapping with other elements
                cv2.putText(frame, f"EMERGENCY CALL: {time_left:.1f}s", (w // 2 - 150, h - 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # Send message also BELOW
                if send_emergency():
                    cv2.putText(frame, "EMERGENCY CALL SENT!", (w // 2 - 120, h - 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "SEND ERROR! TRY AGAIN", (w // 2 - 120, h - 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                gesture_detected = False
                time.sleep(1)
        else:
            gesture_detected = False

        # Fist gesture processing (light control)
        if current_fist_gesture:
            current_time = time.time()
            if not fist_detected:
                fist_detected = True
                fist_start_time = current_time
                print("✊ Fist detected!")

                # Toggle light only if enough time passed since last toggle
                if current_time - last_light_time > light_cooldown:
                    lights_on = not lights_on
                    last_light_time = current_time
                    control_light(lights_on)
        else:
            fist_detected = False

        # ===== Information display with proper positioning =====
        # Top panel - main statuses
        cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
        
        # System status (top left)
        status = "READY" if not gesture_detected else "HOLDING OK"
        cv2.putText(frame, f"STATUS: {status}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Light status (top right)
        light_status = f"Light: {'ON' if lights_on else 'OFF'}"
        cv2.putText(frame, light_status, (w - 150, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if lights_on else (0, 0, 255), 1)

        # Clap counter (top left, under status)
        clap_info = f"Claps: {len(clap_times)}/2"
        cv2.putText(frame, clap_info, (10, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # Clap reset timer
        if clap_timeout_timer > 0:
            time_left = COOLDOWN - (current_time - clap_timeout_timer)
            if time_left > 0:
                cv2.putText(frame, f"Reset in: {time_left:.1f}s", (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)

        # Current gesture (bottom left)
        cv2.putText(frame, f"GESTURE: {current_gesture.upper()}", (10, h - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Instruction (bottom right)
        cv2.putText(frame, "Press 'Q' to quit", (w - 150, h - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Clap information
        cv2.putText(frame, "Clap interval: 1.0-1.5s", (w // 2 - 80, h - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        cv2.imshow("Gesture Control System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n🛑 Program stopped by user")

finally:
    # ===== Cleanup =====
    print("\n🛑 Stopping system...")
    if cap:
        cap.release()
    cv2.destroyAllWindows()

    if stream:
        stream.stop_stream()
        stream.close()
    if p:
        p.terminate()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("✅ System stopped cleanly")
