from flask import Flask, Response, render_template, flash, redirect, session, url_for, request,jsonify
from passlib.hash import pbkdf2_sha256
import uuid
from . import app, db  # Ensure you have a proper module import structure
# from .fire_detection import gen_frames  # Ensure gen_frames is correctly imported
from werkzeug.security import generate_password_hash, check_password_hash  # Not used in this code snippet
from bson import ObjectId
import threading
import pygame
import yagmail
from app.video_feed import gen_frames





# Initialize Pygame for playing sound
pygame.init()
pygame.mixer.init()

# Initialize variables
alarm_playing = False
email_sent = False  # Flag to track if the email has been sent
ip_camera_url = None

# Function to play alarm sound
def play_alarm_sound_function():
    global alarm_playing
    if not alarm_playing:
        alarm_playing = True
        pygame.mixer.music.load('static/fire_alarm.mp3')  # Path to your alarm sound file
        pygame.mixer.music.play()
        print("Fire alarm started")

# Function to stop alarm sound
def stop_alarm_sound_function():
    global alarm_playing
    if alarm_playing:
        pygame.mixer.music.stop()
        alarm_playing = False
        print("Fire alarm stopped")

# # Function to send email
# def send_mail_function():
#     recipientmail = "moolyaswastik48@gmail.com"
#     try:
#         yag = yagmail.SMTP("6+", 'your_password_here')  # Replace with your email and password
#         yag.send(recipientmail, "Warning: Fire accident has been reported")
#         print(f"Alert mail sent successfully to {recipientmail}")
#     except Exception as e:
#         print(f"Error sending email: {e}")

def send_mail_function():
    # Check if the user is logged in
    if 'email' in session:
        recipientmail = session['email']  # Get the logged-in user's email from the session
        try:
            yag = yagmail.SMTP("moolyaswastik48@gmail.com", 'htjf errw gzau ktlg')  # Replace with your email and password
            yag.send(recipientmail, "Warning: Fire accident has been reported")
            print(f"Alert mail sent successfully to {recipientmail}")
        except Exception as e:
            print(f"Error sending email: {e}")
    else:
        print("No user is logged in, unable to send email.")





@app.route('/')
def index():
    return render_template('index.html')



@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    # Logic to use camera_id if necessary
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/profile')
def dashboard():
    return render_template('dashboard.html')

@app.route('/home')
def home():
    
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({'email': email})
        if user and pbkdf2_sha256.verify(password, user['password']):
            session['username'] = user['username']  # Store username in session
            session['email'] = user['email']
            flash('Login successful!', 'login_success')
            return redirect(url_for('home'))  
        else:
            flash('Invalid email or password.', 'login_error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not username or not email or not phone or not password:
            flash('All fields are required!', 'signup_error')
            return redirect(url_for('signup'))

        existing_user = db.users.find_one({'email': email})
        if existing_user:
            flash('Email already exists. Please choose a different email.', 'signup_error')
            return redirect(url_for('signup'))

        hashed_password = pbkdf2_sha256.hash(password)

        new_user = {
            "_id": uuid.uuid4().hex,
            "username": username,
            "email": email,
            "phone": phone,
            "password": hashed_password
        }

        db.users.insert_one(new_user)

        
        return redirect(url_for('login'))
  
    return render_template('signup.html')  # Render signup page for GET requests

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove the username from session
    session.pop('email', None) 
    flash('You have been logged out.', 'logout_success')
    return redirect(url_for('index'))


@app.route('/add_camera', methods=['POST'])
def add_camera():
    global ip_camera_url
    data = request.form
    name = data.get('name')
    ip_address = data.get('ip_address')

    if not ip_address:
        return jsonify({'status': 'error', 'message': 'IP address is required'}), 400

    ip_camera_url = f'rtsp://{ip_address}/stream'
    
    # Store camera details in MongoDB
    camera_id = db.cameras.insert_one({
        'name': name,
        'ip_address': ip_address
    }).inserted_id

    # Respond to the client that the camera has been added successfully
    return jsonify({'status': 'Camera added successfully', 'camera_id': str(camera_id)})


@app.route('/remove_camera/<camera_id>', methods=['POST'])
def remove_camera(camera_id):
    global ip_camera_url

    # Remove camera details from MongoDB
    result = db.cameras.delete_one({'_id': ObjectId(camera_id)})

    if result.deleted_count == 0:
        return jsonify({'status': 'error', 'message': 'Camera not found'}), 404

    # Reset the camera URL if the removed camera was the current one
    if ip_camera_url and ip_camera_url.endswith(camera_id):
        ip_camera_url = None

    return jsonify({'status': 'Camera removed successfully'})

@app.route('/get_cameras', methods=['GET'])
def get_cameras(): 
    cameras = list(db.cameras.find({}, {'_id': 1, 'name': 1, 'ip_address': 1}))
    for camera in cameras:
        camera['_id'] = str(camera['_id'])  # Convert ObjectId to string for JSON serialization
    return jsonify(cameras)

@app.route('/get_camera_url', methods=['GET'])
def get_camera_url():
    return jsonify({'ip_camera_url': ip_camera_url})
