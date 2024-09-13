import cv2
import numpy as np
import threading
import pygame
import smtplib
import math
import cvzone
from ultralytics import YOLO
import yagmail

# Load the YOLO model for fire detection
model = YOLO('best.pt')

# Reading the classes
classnames = ['fire', 'oke']

# Initialize variables
alarm_playing = False

# Function to play alarm sound
def play_alarm_sound_function():
    pygame.mixer.init()
    global alarm_playing
    alarm_playing = True
    pygame.mixer.music.load('fire_alarm.mp3')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(3)
    print("Fire alarm end")
    alarm_playing = False
    pygame.mixer.quit()

# Function to send email
def send_mail_function():
    recipientmail = "moolyaswastik48@gmail.com"
    recipientmail = recipientmail.lower()
    try:
        yag = yagmail.SMTP("moolyaswastik48@gmail.com", 'htjf errw gzau ktlg')
        yag.send(recipientmail, "Warning fire accident has been reported")
        print("Alert mail sent successfully to {}".format(recipientmail))
    except Exception as e:
        print(e)

# Start video capture
vid = cv2.VideoCapture(0)

while True:
    ret, frame = vid.read()
    frame = cv2.resize(frame, (640, 480))
    if not ret:
        print("Error reading frame")
        break

    result = model(frame, stream=True)

    # Getting bbox, confidence, and class names information to work with
    for info in result:
        boxes = info.boxes
        for box in boxes:
            confidence = box.conf[0]
            confidence = math.ceil(confidence * 100)
            Class = int(box.cls[0])
            if confidence > 20 and Class == 0:  # Adjust the confidence threshold and class index
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', [x1 + 8, y1 + 100],
                                   scale=1.5, thickness=2)
                if not alarm_playing:
                    threading.Thread(target=play_alarm_sound_function).start()
                    threading.Thread(target=send_mail_function).start()
                
            
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture
vid.release()
cv2.destroyAllWindows()