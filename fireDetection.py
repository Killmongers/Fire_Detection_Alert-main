from flask import Flask, Response, render_template
import cv2
import threading
import pygame
import requests
import math
import cvzone
from ultralytics import YOLO
app = Flask(__name__)


# Initialize Pygame for playing sound
pygame.init()
pygame.mixer.init()

# Load the YOLO model for fire detection
model = YOLO('best.pt')  # Path to your YOLO model file

# Reading the classes
classnames = ['fire', 'smoke']

# Initialize variables
alarm_playing = False
email_sent = False  # Flag to track if the email has been sent

# Function to play alarm sound
def play_alarm_sound_function():
    global alarm_playing
    if not alarm_playing:
        alarm_playing = True
        pygame.mixer.music.load('fire_alarm.mp3')  # Path to your alarm sound file
        pygame.mixer.music.play()
        print("Fire alarm started")

# Function to stop alarm sound
def stop_alarm_sound_function():
    global alarm_playing
    if alarm_playing:
        pygame.mixer.music.stop()
        alarm_playing = False
        print("Fire alarm stopped")

# Function to send email
def send_mail_function():
  
    url = 'http://localhost:3000/send-email'
    data = {
        
        'to': '',  
        'subject': '',
        'text': ''
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Alert email sent successfully.")
        else:
            print("Failed to send email:", response.text)
    except Exception as e:
        print(f"Error sending email: {e}")


def gen_frames():
    try:
        vid = cv2.VideoCapture(0)
        if not vid.isOpened():
            print("Error: Camera not accessible.")
            return

        while True:
            success, frame = vid.read()
            if not success:
                print("Error reading frame")
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
                    if confidence > 50:
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                        cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', [x1 + 8, y1 + 100], scale=1.5, thickness=2)
                        detected_fire = True

            if detected_fire:
                if not alarm_playing:
                    threading.Thread(target=play_alarm_sound_function).start()
                if not email_sent:
                    threading.Thread(target=send_mail_function).start()
                    email_sent = True
            else:
                stop_alarm_sound_function()
                email_sent = False

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Error encoding frame")
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        vid.release()
        pygame.mixer.quit()
        cv2.destroyAllWindows()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)



