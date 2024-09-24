import cv2
import math
import cvzone
from ultralytics import YOLO
import pygame
import threading
import time
from datetime import datetime
import requests



model = YOLO('best.pt')
classnames = ['fire']

alarm_playing = False
fire_detected = False
fire_alert_triggered = False 

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
        alarm_playing = False
def trigger_fire_alert(camera_name, user_id, user_email):
    try:
        response = requests.post(
            "http://localhost:5000/send-alert",
            json={"camera_name": camera_name, "user_id": user_id, "email": user_email}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def gen_frames(ip_camera_url, camera_name, user_id, user_email):
    global fire_alert_triggered

    while True:
        try:
            vid = cv2.VideoCapture(ip_camera_url) 
            if not vid.isOpened():
                time.sleep(10)
                continue

            while True:
                success, frame = vid.read()
                if not success:
                    break

                frame = cv2.resize(frame, (640, 480))

                now = datetime.now()
                date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, date_time_str, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                result = model(frame, stream=True)

                detected_fire = False
                for info in result:
                    boxes = info.boxes
                    for box in boxes:
                        confidence = box.conf[0]
                        confidence = math.ceil(confidence * 100)
                        Class = int(box.cls[0])
                        if confidence > 50 and Class == 0:
                            x1, y1, x2, y2 = box.xyxy[0]
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                            cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', [x1 + 8, y1 + 100], scale=1.5, thickness=2)
                            detected_fire = True

                if detected_fire:
                    if not fire_alert_triggered:
                        print("alert triggered")
                        trigger_fire_alert(camera_name, user_id, user_email)  
                        threading.Thread(target=play_alarm_sound_function).start()
                        fire_alert_triggered = True
                else:
                    if fire_alert_triggered:
                        fire_alert_triggered = False

                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        except Exception as e:
            print(f"Error in video stream: {e}")
        finally:
            vid.release()
            print("Camera connection closed. Reconnecting...")
