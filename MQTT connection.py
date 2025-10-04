#Before you start installing libraries and coding, install the firmware 13.04.0 for ESP8266 listed on the homepage, I installed it via Tasmotizer using my (bin) image
# On Raspberry Pi 4:
# Complete installation
sudo apt remove --purge mosquitto mosquitto-client  # If installed incorrectly
sudo rm -rf /etc/mosquitto/ /var/log/mosquitto/  # If installed incorrectly
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable mosquitto  # Auto-start on Raspberry Pi boot
sudo systemctl start mosquitto

sudo nano /etc/mosquitto/mosquitto.conf
# Add:

listener 1883
allow_anonymous true

sudo systemctl restart mosquitto

# Verify MQTT is working:
# Terminal 1 - subscription (listen for messages)
mosquitto_sub -h localhost -t "test" -v

# Terminal 2 - publication (send message)
mosquitto_pub -h localhost -t "test" -m "hello"

# Subscribe to Tasmota topics:
mosquitto_sub -h localhost -t "tele/#" -v

# Find IP for ESP on Raspberry Pi:
hostname -I

# On ESP:
# Download Tasmotizer, install firmware
# Then connect to wifi and MQTT by entering the Raspberry Pi IP we found earlier

# Configuration --> Module --> GPIO2 LED1

# After loading code on Raspberry Pi 4, install paho-mqtt library:
pip3 install paho-mqtt

# Main code:
import cv2
import mediapipe as mp
import time
import paho.mqtt.client as mqtt
import json

# ===== MQTT Settings =====
MQTT_BROKER = ""  # Your Raspberry Pi IP - set it yourself!!!!!
MQTT_PORT = 1883
MQTT_TOPIC = "cmnd/tasmota_DEE65D/POWER"
MQTT_USER = "DVES_USER"  # if exists
MQTT_PASS = "147"  # if exists

# ===== MQTT Client =====
mqtt_client = mqtt.Client()

# If authentication required:
# mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)

def connect_mqtt():
    """Connect to MQTT broker"""
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("Connected to MQTT broker")
        return True
    except Exception as e:
        print(f"MQTT connection error: {e}")
        return False

def control_light(state):
    """Control light on ESP8266"""
    command = "ON" if state else "OFF"
    try:
        mqtt_client.publish(MQTT_TOPIC, command)
        print(f"Command sent: {command}")
    except Exception as e:
        print(f"Command sending error: {e}")

# ===== System State =====
class SystemState:
    pass

state = SystemState()
state.lights_on = False
state.last_time = 0
state.cooldown = 2  # delay between gestures

# ===== MediaPipe =====
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# ===== Connect MQTT =====
if not connect_mqtt():
    print("Working without MQTT (simulation only)")

cap = cv2.VideoCapture(0)

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

print("Starting light control system...")
print("Gestures: Fist - toggle light, Q - exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)  # mirror
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    gesture = "none"
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = detect_gesture(hand_landmarks, h, w)

    # toggle light with fist
    if gesture == "fist" and time.time() - state.last_time > state.cooldown:
        state.lights_on = not state.lights_on
        state.last_time = time.time()

        # Control real light on ESP8266
        control_light(state.lights_on)

        print(f"Light toggled: {'ON' if state.lights_on else 'OFF'}")

    # ===== On-screen text =====
    status_text = f"Light: {'ON' if state.lights_on else 'OFF'}"
    gesture_text = f"Gesture: {gesture}"

    cv2.putText(frame, status_text, (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if state.lights_on else (0, 0, 255), 2)

    cv2.putText(frame, gesture_text, (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, "Q - quit", (50, h - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Light Control by Gesture", frame)

    if cv2.waitKey(5) & 0xFF == ord("q"):
        break

# ===== Cleanup =====
cap.release()
cv2.destroyAllWindows()
mqtt_client.loop_stop()
mqtt_client.disconnect()
print("System stopped")


# If connection fails, reconnect and reboot ESP

