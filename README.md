![GitHub Repo stars](https://img.shields.io/github/stars/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant?style=for-the-badge&color=blue) ![GitHub watchers](https://img.shields.io/github/watchers/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant?style=for-the-badge&label=Views&color=green) ![GitHub top language](https://img.shields.io/github/languages/top/Smashing1234/Raspberry-4-smart-gesture-recognition-assistant?style=for-the-badge&color=orange)
# Raspberry 4 smart gesture recognition assistant
Raspberry 4 smart gesture recognition assistant is an innovative gesture recognition system that creates a bridge between the world of the deaf and technology. It helps people with hearing impairments control their smart homes, call for emergency assistance, and receive information through simple gestures.

## Purpose and description
Now I will explain step by step how I was able to implement this project. Before I start, I'll tell you what the point of all this is. I did this project to solve one of the social problems of the deaf and people with disabilities, I think it can give rise to something bigger and better.  My project is a kind of "voice assistant" Siri, Alice, and so on. Based on them, I made this project. My project can recognize gestures such as fist and the "OK" gesture, as well as recognize claps, while performing various tasks. The first task is to turn on and off a relay with an LED that simulates light, with two claps or clenching and unclenching of a fist.  Another task is to notify relatives to whom emergency messages are sent with an "OK" gesture.

## Research objectives:
- Analysis of communication needs of deaf and mute users
- Development of gesture recognition algorithms
- Implementation of the vibration feedback system
- Integration with the smart home platform via MQTT
- Creation of an emergency notification mechanism

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

## Conclusions
The developed system demonstrates the effectiveness of gesture control for deaf and dumb users, providing them with equal access to smart home technologies and increasing the level of independence and security.
