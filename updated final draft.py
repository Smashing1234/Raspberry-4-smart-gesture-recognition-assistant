import cv2
import mediapipe as mp
import time
import requests
import paho.mqtt.client as mqtt
import pyaudio
import numpy as np
import Adafruit_DHT as dht
import threading
from datetime import datetime
from rpi_lcd import LCD

lcd = LCD()
DHT_SENSOR = dht.DHT11
DHT_PIN = 14

lcd_lock = threading.Lock()
current_line1 = "Starting..."
current_line2 = "Please wait"
display_mode = "temp_hum"
last_temp_update = 0
temp_update_interval = 5
log_display_start = 0
log_display_duration = 8

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

MQTT_BROKER = "" #ip raspberry pi 4
MQTT_PORT = 1883
MQTT_TOPIC = "cmnd/sonoff/POWER"
MQTT_USER = "DVES_USER"
MQTT_PASS = "147"

CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD = 2500

DOUBLE_CLAP_MIN_TIMEOUT = 1.0
DOUBLE_CLAP_MAX_TIMEOUT = 1.5
COOLDOWN = 2.0
call_cooldown = 300
hold_time_needed = 2
max_distance = 24
light_cooldown = 1.0

clap_times = []
lights_on = False
last_light_time = 0
clap_timeout_timer = 0
last_call_time = 0
gesture_start_time = 0
gesture_detected = False
fist_start_time = 0
fist_detected = False

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.9)
mp_draw = mp.solutions.drawing_utils

def update_lcd_display():
    global display_mode, last_temp_update, log_display_start

    while True:
        with lcd_lock:
            current_time = time.time()

            if display_mode == "temp_hum":
                if current_time - last_temp_update >= temp_update_interval:
                    try:
                        humidity, temperature = dht.read_retry(DHT_SENSOR, DHT_PIN)
                        if humidity is not None and temperature is not None:
                            current_line1 = f"Temp:{temperature:.1f}C"
                            current_line2 = f"Hum:{humidity:.1f}%"
                            lcd.text(current_line1, 1)
                            lcd.text(current_line2, 2)
                            last_temp_update = current_time
                        else:
                            current_line1 = "DHT11 Error"
                            current_line2 = "Check sensor"
                            lcd.text(current_line1, 1)
                            lcd.text(current_line2, 2)
                    except Exception as e:
                        current_line1 = "DHT11 Error"
                        current_line2 = str(e)[:16]
                        lcd.text(current_line1, 1)
                        lcd.text(current_line2, 2)
                        last_temp_update = current_time

            elif display_mode == "log":
                if current_time - log_display_start > log_display_duration:
                    display_mode = "temp_hum"
                    last_temp_update = 0
                else:
                    lcd.text(current_line1[:16], 1)
                    lcd.text(current_line2[:16] if current_line2 else "", 2)

        time.sleep(0.5)

def show_log_on_lcd(line1, line2=""):
    global display_mode, current_line1, current_line2, log_display_start

    with lcd_lock:
        current_line1 = line1
        current_line2 = line2
        display_mode = "log"
        log_display_start = time.time()

        lcd.text(current_line1[:16], 1)
        lcd.text(current_line2[:16] if current_line2 else "", 2)

lcd_thread = threading.Thread(target=update_lcd_display, daemon=True)
lcd_thread.start()

show_log_on_lcd("System", "starting...")
time.sleep(2)

try:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not available")
        show_log_on_lcd("Camera", "not available")
        cap = None
    else:
        print("✅ Camera initialized")
        show_log_on_lcd("Camera", "initialized")
except Exception as e:
    print(f"❌ Camera initialization failed: {e}")
    show_log_on_lcd("Camera", "init failed")
    cap = None

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

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
    show_log_on_lcd("Microphone", "initialized")
except Exception as e:
    print(f"❌ Microphone initialization failed: {e}")
    show_log_on_lcd("Microphone", "init failed")
    p = None
    stream = None

def connect_mqtt():
    try:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        time.sleep(1)
        print("✅ Connected to MQTT broker")
        show_log_on_lcd("MQTT", "connected")
        return True
    except Exception as e:
        print(f"❌ MQTT connection error: {e}")
        show_log_on_lcd("MQTT", "failed")
        return False

def control_light(state):
    global lights_on
    try:
        if state:
            mqtt_client.publish(MQTT_TOPIC, "ON")
            print("💡 Команда ON отправлена")
            show_log_on_lcd("Light", "ON")
        else:
            mqtt_client.publish(MQTT_TOPIC, "OFF")
            print("💡 Команда OFF отправлена")
            show_log_on_lcd("Light", "OFF")

        lights_on = state
        return True
    except Exception as e:
        print(f"❌ Command sending error: {e}")
        show_log_on_lcd("Light", "error")
        return False

def toggle_light():
    global lights_on
    try:
        mqtt_client.publish(MQTT_TOPIC, "TOGGLE")
        lights_on = not lights_on
        print(f"🔄 Light toggled to {'ON' if lights_on else 'OFF'}")
        show_log_on_lcd("Light", f"{'ON' if lights_on else 'OFF'}")
        return True
    except Exception as e:
        print(f"❌ Toggle command error: {e}")
        show_log_on_lcd("Toggle", "error")
        return False

def send_emergency():
    global last_call_time
    current_time = time.time()

    if current_time - last_call_time < call_cooldown:
        print("⏳ Emergency call on cooldown")
        show_log_on_lcd("Call", "cooldown")
        return False

    try:
        print("📡 Sending emergency message...")
        show_log_on_lcd("Sending", "emergency")

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': "🚨 EMERGENCY CALL 🚨\n\nUser needs help! Please check immediately."
        }

        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            last_call_time = current_time
            print("✅ Emergency call sent successfully!")
            show_log_on_lcd("Emergency", "sent!")
            return True
        else:
            print(f"❌ Failed to send. Status: {response.status_code}")
            show_log_on_lcd("Send", "failed")
            return False

    except Exception as e:
        print(f"❌ Error sending message: {e}")
        show_log_on_lcd("Send", "error")
        return False

def is_finger_extended(pip, dip, tip):
    return tip[1] < pip[1] and tip[1] < dip[1]

def detect_gesture(landmarks, h, w):
    lm = [(int(p.x * w), int(p.y * h)) for p in landmarks.landmark]

    fingers = []
    fingers.append(1 if lm[4][0] > lm[3][0] else 0)
    for tip in [8, 12, 16, 20]:
        fingers.append(1 if lm[tip][1] < lm[tip - 2][1] else 0)

    if sum(fingers) == 0:
        return "fist"
    elif sum(fingers) == 5:
        return "palm"
    else:
        return "other"

def is_clap(audio_data):
    volume = np.max(np.abs(audio_data))
    return volume > THRESHOLD, volume

def process_audio_fast():
    global clap_times, lights_on, last_light_time, clap_timeout_timer

    if stream is None:
        return

    try:
        data = stream.read(CHUNK, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        current_time = time.time()

        detected, volume = is_clap(audio_data)

        if detected and volume > THRESHOLD:
            print(f"👏 Clap! Volume: {volume}")
            show_log_on_lcd("Clap", "detected")

            clap_times.append(current_time)

            if len(clap_times) > 2:
                clap_times = clap_times[-2:]

            clap_timeout_timer = current_time

            if len(clap_times) == 2:
                interval = clap_times[1] - clap_times[0]
                print(f"📊 Interval: {interval:.3f}s")

                if DOUBLE_CLAP_MIN_TIMEOUT <= interval <= DOUBLE_CLAP_MAX_TIMEOUT:
                    if current_time - last_light_time > light_cooldown:
                        toggle_light()
                        last_light_time = current_time
                        clap_times = []
                        clap_timeout_timer = 0
                else:
                    print(f"❌ Invalid interval: {interval:.3f}s")
                    show_log_on_lcd("Clap", "bad interval")
                    clap_times = [clap_times[1]]

        if clap_timeout_timer > 0 and (current_time - clap_timeout_timer) > COOLDOWN:
            print("🔄 Clap timer reset")
            clap_times = []
            clap_timeout_timer = 0

    except Exception as e:
        print(f"❌ Audio processing error: {e}")

def test_telegram_connection():
    print("🔍 Testing Telegram...")
    show_log_on_lcd("Testing", "Telegram")

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram bot is working!")
            show_log_on_lcd("Telegram", "OK")
            return True
        else:
            print(f"❌ Bot test failed: {response.status_code}")
            show_log_on_lcd("Telegram", "failed")
            return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        show_log_on_lcd("Telegram", "error")
        return False

connect_mqtt()
time.sleep(1)
test_telegram_connection()
time.sleep(1)

print("\n🚀 System started!")
show_log_on_lcd("System", "started")
time.sleep(1)

print("Gestures:")
print("  - Fist: toggle light")
print("  - OK (hold 2 sec): emergency call")
print("Claps:")
print("  - Double clap (1.0-1.5s): toggle light")
print("Press 'Q' to quit\n")

try:
    while True:
        process_audio_fast()

        if cap is not None:
            success, frame = cap.read()
            if success:
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                current_ok_gesture = False
                current_fist_gesture = False
                current_gesture = "none"

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        landmarks = []
                        for point in hand_landmarks.landmark:
                            x = int(point.x * w)
                            y = int(point.y * h)
                            landmarks.append((x, y))

                        thumb_tip = landmarks[4]
                        index_tip = landmarks[8]
                        middle_tip = landmarks[12]
                        ring_tip = landmarks[16]
                        pinky_tip = landmarks[20]

                        index_pip = landmarks[6]
                        index_dip = landmarks[7]
                        middle_pip = landmarks[10]
                        middle_dip = landmarks[11]
                        ring_pip = landmarks[14]
                        ring_dip = landmarks[15]
                        pinky_pip = landmarks[18]
                        pinky_dip = landmarks[19]

                        dx = thumb_tip[0] - index_tip[0]
                        dy = thumb_tip[1] - index_tip[1]
                        distance = (dx * dx + dy * dy) ** 0.5

                        middle_extended = is_finger_extended(middle_pip, middle_dip, middle_tip)
                        ring_extended = is_finger_extended(ring_pip, ring_dip, ring_tip)
                        pinky_extended = is_finger_extended(pinky_pip, pinky_dip, pinky_tip)

                        if (distance < max_distance and
                                middle_extended and
                                ring_extended and
                                pinky_extended):
                            current_ok_gesture = True

                        current_gesture = detect_gesture(hand_landmarks, h, w)
                        if current_gesture == "fist":
                            current_fist_gesture = True

                current_time = time.time()

                if current_ok_gesture:
                    if not gesture_detected:
                        gesture_detected = True
                        gesture_start_time = current_time
                        print("👌 OK gesture detected")
                        show_log_on_lcd("OK gesture", "hold 2 sec")

                    hold_time = current_time - gesture_start_time
                    time_left = hold_time_needed - hold_time

                    if time_left > 0:
                        cv2.putText(frame, f"EMERGENCY: {time_left:.1f}s",
                                    (w // 2 - 150, h - 100),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        print("🆘 Sending emergency...")
                        if send_emergency():
                            cv2.putText(frame, "EMERGENCY SENT!",
                                        (w // 2 - 120, h - 100),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        else:
                            cv2.putText(frame, "SEND ERROR!",
                                        (w // 2 - 120, h - 100),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        gesture_detected = False
                else:
                    gesture_detected = False

                if current_fist_gesture:
                    current_time = time.time()
                    if not fist_detected:
                        fist_detected = True
                        fist_start_time = current_time
                        print("✊ Fist detected!")
                        show_log_on_lcd("Fist", "detected")

                        if current_time - last_light_time > light_cooldown:
                            toggle_light()
                            last_light_time = current_time
                else:
                    fist_detected = False

                cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)

                status = "READY" if not gesture_detected else "HOLDING OK"
                cv2.putText(frame, f"STATUS: {status}", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                light_status = f"Light: {'ON' if lights_on else 'OFF'}"
                cv2.putText(frame, light_status, (w - 150, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0) if lights_on else (0, 0, 255), 1)

                clap_info = f"Claps: {len(clap_times)}/2"
                cv2.putText(frame, clap_info, (10, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                cv2.putText(frame, f"Gesture: {current_gesture.upper()}",
                            (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (200, 200, 200), 1)

                cv2.putText(frame, "Press 'Q' to quit",
                            (w - 150, h - 40), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255), 1)

                cv2.imshow("Gesture Control System", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            show_log_on_lcd("System", "stopped")
            break

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user")
    show_log_on_lcd("Stopped", "by user")

except Exception as e:
    print(f"❌ Error: {e}")
    show_log_on_lcd("Error", str(e)[:16])

finally:
    print("\n🛑 Stopping system...")
    show_log_on_lcd("Shutting", "down...")
    time.sleep(2)

    if cap:
        cap.release()
    cv2.destroyAllWindows()

    if stream:
        stream.stop_stream()
        stream.close()
    if p:
        p.terminate()

    with lcd_lock:
        lcd.clear()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("✅ System stopped cleanly")