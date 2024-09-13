import cv2
import math
import cvzone
from ultralytics import YOLO
import pygame
import threading
import yagmail

# Load the YOLO model for fire detection
model = YOLO('app/best.pt')  # Path to your YOLO model file
classnames = ['fire', 'smoke']

# Initialize variables
alarm_playing = False
email_sent = False
ip_camera_url = ""

# Function to play alarm sound
def play_alarm_sound_function():
    global alarm_playing
    if not alarm_playing:
        pygame.mixer.init()
        alarm_playing = True
        pygame.mixer.music.load('fire_alarm.mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(3)
        pygame.mixer.quit()
        print("Fire alarm end")
        alarm_playing = False

# Function to stop alarm sound
def stop_alarm_sound_function():
    global alarm_playing
    if alarm_playing:
        pygame.mixer.music.stop()
        alarm_playing = False
        pygame.mixer.quit()

# Function to send email
def send_mail_function():
    recipientmail = "Harshbhatiya17052002@gmail.com"
    recipientmail = recipientmail.lower()
    try:
        yag = yagmail.SMTP("moolyaswastik48@gmail.com", 'htjf errw gzau ktlg')  # Replace with actual credentials
        yag.send(recipientmail, "Warning: Fire accident has been reported")
        print(f"Alert mail sent successfully to {recipientmail}")
    except Exception as e:
        print(e)

def gen_frames():
    global ip_camera_url
    vid = cv2.VideoCapture(ip_camera_url)
    if not vid.isOpened():
        print("Error: Camera not accessible.")
        return

    while True:
        success, frame = vid.read()
        if not success:
            break

        frame = cv2.resize(frame, (640, 480))
        result = model(frame, stream=True)

        detected_fire = False
        for info in result:
            boxes = info.boxes
            for box in boxes:
                confidence = box.conf[0]
                confidence = math.ceil(confidence * 100)
                Class = int(box.cls[0])
                if confidence > 50 and Class == 0:  # Adjust thresholds as needed
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                    cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', [x1 + 8, y1 + 100], scale=1.5, thickness=2)
                    detected_fire = True

        if detected_fire:
            if not email_sent:
                threading.Thread(target=play_alarm_sound_function).start()
                threading.Thread(target=send_mail_function).start()
                email_sent = True
        else:
            stop_alarm_sound_function()
            email_sent = False

        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield raw JPEG data
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    vid.release()
