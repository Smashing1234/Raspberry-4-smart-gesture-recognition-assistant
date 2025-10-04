# Before you start, create a bot in telegram, get a unique API from it, and also find out from those who will need to send messages their telegram ID.
# The command to install the library on Raspberry
pip3 install python-telegram-bot

import cv2
import mediapipe as mp
import time
import requests
import paho.mqtt.client as mqtt

# ===== Settings =====
TELEGRAM_BOT_TOKEN = "" # Bot API token in Telegram
TELEGRAM_CHAT_ID = "" # User ID

# ===== MQTT Settings =====
MQTT_BROKER = ""  # Raspberry Pi IP
MQTT_PORT = 1883
MQTT_TOPIC = "cmnd/tasmota_DEE65D/POWER"
MQTT_USER = "DVES_USER"
MQTT_PASS = "147"

# ===== Variables =====
last_call_time = 0
call_cooldown = 300  # 5 minutes between calls
hold_time_needed = 2  # 2 seconds holding time
max_distance = 24  # 24 pixels between fingers

# ===== Initialization =====
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
cap = cv2.VideoCapture(0)

# ===== MQTT Client =====
mqtt_client = mqtt.Client()

def connect_mqtt():
    """Connect to MQTT broker"""
    try:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
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

# ===== Message sending function =====
def send_emergency():
    global last_call_time
    current_time = time.time()

    if current_time - last_call_time < call_cooldown:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': "🚨 EMERGENCY CALL 🚨\n\nUser needs help!"
        }
        response = requests.post(url, data=data, timeout=5)
        last_call_time = current_time
        return response.status_code == 200
    except:
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

# ===== Connect MQTT =====
if not connect_mqtt():
    print("Working without MQTT (simulation only)")

# ===== Main loop =====
gesture_start_time = 0
gesture_detected = False
fist_start_time = 0
fist_detected = False
lights_on = False
light_cooldown = 2  # delay between light toggles
last_light_time = 0

print("System started!")
print("Gestures:")
print("  - Fist: turn light on/off")
print("  - OK (2 sec): emergency call")

while True:
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
        for hand in results.multi_hand_landmarks:
            # Get finger points
            landmarks = []
            for point in hand.landmark:
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
            current_gesture = detect_gesture(hand, h, w)
            if current_gesture == "fist":
                current_fist_gesture = True

    # OK gesture processing
    current_time = time.time()

    if current_ok_gesture:
        if not gesture_detected:
            gesture_detected = True
            gesture_start_time = current_time
            print("OK gesture detected...")

        # Calculate remaining time
        hold_time = current_time - gesture_start_time
        time_left = hold_time_needed - hold_time

        if time_left > 0:
            # Show countdown
            cv2.putText(frame, f"EMERGENCY CALL: {time_left:.1f}s", (w // 2 - 150, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Send message
            if send_emergency():
                cv2.putText(frame, "CALL SENT!", (w // 2 - 70, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                print("Emergency call sent!")
            else:
                cv2.putText(frame, "ERROR!", (w // 2 - 40, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            gesture_detected = False
            time.sleep(2)
    else:
        gesture_detected = False

    # Fist gesture processing (light control)
    if current_fist_gesture:
        if not fist_detected:
            fist_detected = True
            fist_start_time = current_time
            print("Fist detected!")

            # Toggle light only if enough time passed since last toggle
            if current_time - last_light_time > light_cooldown:
                lights_on = not lights_on
                last_light_time = current_time
                control_light(lights_on)
                print(f"Light toggled: {'ON' if lights_on else 'OFF'}")

    else:
        fist_detected = False

    # Display information (top panel)
    cv2.rectangle(frame, (0, 0), (w, 30), (0, 0, 0), -1)
    status = "READY" if not gesture_detected else "HOLDING OK"
    cv2.putText(frame, f"STATUS: {status}", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.putText(frame, f"LIGHT: {'ON' if lights_on else 'OFF'}", (w - 120, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if lights_on else (0, 0, 255), 1)

    # Display current gesture
    cv2.putText(frame, f"CURRENT GESTURE: {current_gesture.upper()}", (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Instruction at bottom
    cv2.putText(frame, "Press 'Q' to quit", (w - 150, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Gesture Control System", frame)

    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
mqtt_client.loop_stop()
mqtt_client.disconnect()
print("System stopped")