![GitHub Repo stars](https://img.shields.io/github/stars/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant?style=for-the-badge&color=blue) ![GitHub watchers](https://img.shields.io/github/watchers/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant?style=for-the-badge&label=Views&color=green) ![GitHub top language](https://img.shields.io/github/languages/top/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant?style=for-the-badge&color=orange)
# Raspberry 4 smart gesture recognition assistant
The main motivation behind the project is to help people with hearing impairments gain easy access to smart home technologies. Since voice assistants are useless for them, and wearable devices like hearing-impaired gloves are not always convenient, the Smart Gesture Station was created. It is a prototype based on Raspberry Pi that uses a camera to recognize intuitive gestures, allowing users to control their homes and send emergency signals quickly, without the need for voice.

## Purpose and description
Now I will explain step by step how I was able to implement this project. Before I start, I'll tell you what the point of all this is. I did this project to solve one of the social problems of the deaf and people with disabilities, I think it can give rise to something bigger and better.  My project is a kind of "voice assistant" Siri, Alice, and so on. Based on them, I made this project. My project can recognize gestures such as fist and the "OK" gesture, as well as recognize claps, while performing various tasks. The first task is to turn on and off a relay with an LED that simulates light, with two claps or clenching and unclenching of a fist.  Another task is to notify relatives to whom emergency messages are sent with an "OK" gesture.

## Project objectives:
- Develop an algorithm for recognizing intuitive gestures (fist, "OK") and sound patterns (clap) based on computer vision and audio analysis libraries.
- Implement a wireless device control module using the MQTT protocol and an emergency notification system using the Telegram Bot API.
- Design, build, and programmatically configure a hardware prototype based on Raspberry Pi with a camera, microphone, and feedback modules (LCD display, sensors).
- Test the prototype's functionality by evaluating its recognition accuracy, response latency, and overall practical applicability.
  
## Performance

https://github.com/user-attachments/assets/2430dc74-bb1f-4c9f-a8ee-8e46b0dc5894

# Step-by-step implementation plan

## Part 1. Necessary resources
For this project, we will need:
Raspberry 4 or 5, Power supply, SD card from 16 GB, the more the better, a camera that works on USB, a microphone is also USB, but I have a microphone built into the camera, a wire with a miniHDMI connector, a monitor, a keyboard, a mouse. For the second part of the project with the connection of the relay via the MQTT protocol, you will need:
ESP8266, a power supply for it, see the relay in the photo, a breadboard, but you can also use it without it, wires, an LED, a resistor. You definitely need a PC and an Internet connection.

![IMG_3336 (2)](https://github.com/user-attachments/assets/485a997f-3fd9-454a-a977-d546a491f7b0)

## Part 2. The first introduction to Raspberry
The very first thing you need to do is download the system image 2025-05-06-raspios-bullseye-arm64.img.xz (you can install its archive by going to the main [window](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/2025-05-06-raspios-bullseye-arm64.img.xz.torrent ) and install it on the SD using the Raspberry Pi Imager program. To do this, run the Raspberry Pi Imager program, select which device you will install on, and then select with another button that you want to use your img image. And install it

<img width="680" height="480" alt="image" src="https://github.com/user-attachments/assets/2e958e31-4f34-453b-839f-ccad278bf7c0" />

## Part 3. Installing libraries for hand recognition. OpenCV. Mediapipe. Hand recognition
The next step is to download the libraries for gesture recognition and camera control, you can see it [here](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/Hand%20recognition.py)

## Part 4. Installing Tasmota. MQTT. Fist gesture. ESP8266. Turning lights on and off with a fist gesture
In the next step, we will be able to control the ESP8266 using Raspberry 4, you can see it [here](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/MQTT%20connection.py) and you can download the Tasmota version [here](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/tasmota.bin)

<img width="492" height="459" alt="image" src="https://github.com/user-attachments/assets/858af6f7-f63c-4ed2-a995-c1088fb93cbe" />

To download firmware 13.04.0, you need to download Tasmotizer and select your BIN file in it.

## Part 5. Pyaudio. microphone. Claps recognition
In this step, I've figured out how to recognize claps using a microphone, you can see it [here](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/Clap%20recognition.py)

## Part 6. Sending notifications to Telegram. The "OK" gesture. Fist gesture. API Bot Telegram
Here I was able to initialize the OK gesture, after which a telegram notification is sent. I also connected it with a 4-part code, you can see it [here](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/Sending%20notifications%20in%20telegram.py)

## Part 7. Usage: ESP8266, Relay, MQTT, Tasmota, LED, Resistor, Clap recognition, gesture recognition
Here I combined all the parts into one, using a relay and an LED and a resistor, you can see it [here](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/blob/main/Connecting%20Relay.py)

![photo_2025-10-11_10-55-32](https://github.com/user-attachments/assets/83e17a95-42ed-482b-8ba0-95bdaffbf7cb)

# Key changes/improvements for 2026:

## Part 8.1. Upgrade to Sonoff R4
I changed the esp8266 to an esp32. The esp32 and the relay were built into the sonoff R4 module, so I only had to flash the esp32 and install Tasmota.

<img width="353" height="810" alt="tasmota 1 1 jpg" src="https://github.com/user-attachments/assets/d2554f68-296f-47e2-b05a-c3390a4b4c2d" />

## Part 8.2. Creating a case
In order to make my project look like a regular mini-station, I had to create and print a 3D model of the [case](https://github.com/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant/commit/7dd63af01491b17ffcb7aef9a9fa4ca3d35caa46). Keep in mind that I already have active cooling for the case, which significantly changes the original dimensions.

<img width="926" height="743" alt="весь корпус" src="https://github.com/user-attachments/assets/4a02ab51-2de7-46a6-8145-94737e3895e5" />

## Part 8.3. Display and temperature sensor
I also added the lcd1602 display (using the i2c protocol) and the DHT11 module to the project. Information about [lcd1602](https://peppe8o.com/1602-lcd-raspberry-pi-display/) and information about [dht11](https://www.raspberrypi-5.com/how-to-connect/how-to-connect-dht11-to-raspberry-pi/)

![photo_4_2026-01-31_09-54-09](https://github.com/user-attachments/assets/01d97ac1-b48b-4dd1-8be1-a830fbf975f2)

## Part 8.4. Mini conclusion
In general, the changes were more visual. I switched to a ready-made version in the form of a sonoff R4, and I also used a screen to display the program's status, including temperature and humidity data.

## Results
To test the concept, a functional prototype of the system was assembled and implemented in software. In practice, it was possible to verify how the theoretical principles — lightweight geometric gesture analysis instead of ML, local data processing, and a modular architecture — are implemented in a real device. 

- Results of the total delay of the fist recognition (from recognition to changing the relay state):

<img width="743" height="430" alt="График кулаков в2" src="https://github.com/user-attachments/assets/61707994-d9af-47b8-8547-83173c7d237e" />

- Results of the total double-tap recognition delay (from recognition to change of the retransmission status):

<img width="843" height="261" alt="График хлопков в2" src="https://github.com/user-attachments/assets/188750c7-374e-4fa3-bf16-6070a07063a2" />

- Program completion percentage results:

<img width="1140" height="757" alt="Проц выпол в2" src="https://github.com/user-attachments/assets/72d5b394-a838-48ba-ae57-6cd107a250e1" />

## Conclusion
A working prototype of an assistive system has been created. This prototype proves the possibility of recognizing gestures using a camera and lightweight algorithms on a Raspberry Pi. It functions as a prototype of a local platform for controlling devices over Wi-Fi and sending emergency alerts, offering a practical prototype of a solution for contactless interaction with a smart home. Recognition accuracy: 80% (gestures), 65% (claps), execution delays vary from 1.5 to 3 seconds depending on the action
