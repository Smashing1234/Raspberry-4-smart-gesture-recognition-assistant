# Raspberry 4 smart gesture recognition assistant
Raspberry 4 smart gesture recognition assistant is an innovative gesture recognition system that creates a bridge between the world of the deaf and technology. It helps people with hearing impairments control their smart homes, call for emergency assistance, and receive information through simple gestures.


Now I will explain step by step how I was able to implement this project. Before I start, I'll tell you what the point of all this is. I did this project to solve one of the social problems of the deaf and people with disabilities, I think it can give rise to something bigger and better.  My project is a kind of "voice assistant" Siri, Alice, and so on. Based on them, I made this project. My project can recognize gestures such as fist and the "OK" gesture, as well as recognize claps, while performing various tasks. The first task is to turn on and off a relay with an LED that simulates light, with two claps or clenching and unclenching of a fist.  Another task is to notify relatives to whom emergency messages are sent with an "OK" gesture.

For this project, we will need:
Raspberry 4 or 5, Power supply, SD card from 16 GB, the more the better, a camera that works on USB, a microphone is also USB, but I have a microphone built into the camera, a wire with a miniHDMI connector, a monitor, a keyboard, a mouse. For the second part of the project with the connection of the relay via the MQTT protocol, you will need:
ESP8266, a power supply for it, see the relay in the photo, a breadboard, but you can also use it without it, wires, an LED, a resistor. You definitely need a PC and an Internet connection.

![IMG_3336 (2)](https://github.com/user-attachments/assets/485a997f-3fd9-454a-a977-d546a491f7b0)
