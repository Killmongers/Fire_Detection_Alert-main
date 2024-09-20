from flask import Flask, Response, render_template, flash, redirect, session, url_for, request, jsonify
from passlib.hash import pbkdf2_sha256
import uuid
from . import app, db  # Ensure you have a proper module import structure
from bson import ObjectId
import threading
import pygame
import yagmail
from app.video_feed import gen_frames
from datetime import datetime



@app.route('/pause')
def pause_video():
    global video_paused
    video_paused = True
    return "Video paused"

@app.route('/start')
def start_video():
    global video_paused
    video_paused = False
    return "Video started"

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    user_id = session.get('user_id')
    user_email = session.get('email')

    # Ensure user is authenticated
    if not user_id or not user_email:
        return "User not authenticated", 403

    # Fetch camera details from the database
    camera = db.cameras.find_one({'_id': ObjectId(camera_id), 'user_id': user_id})
    
    if camera is None:
        return "Camera not found or access denied", 404

    ip_address = camera.get('ip_address')  # Adjust this key based on your database schema

    return Response(gen_frames(ip_address, camera['name'], user_id, user_email), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/profile')
def dashboard():
    return render_template('dashboard.html')


@app.route('/home')
def home():
    print(session)
    
    if 'username' in session and 'email' in session:
        return render_template('home.html', username=session['username'])
    
    return redirect(url_for('login'))


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({'email': email})
        if user and pbkdf2_sha256.verify(password, user['password']):
            session['username'] = user['username']
            session['user_id'] = str(user['_id'])  # Ensure user ID is converted to string
            session['email'] = user['email']
            
          
            flash('Login successful!', 'login_success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'login_error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/send-alert', methods=['POST'])
def send_alert():
    # Get the request data
    request_data = request.get_json()
    print("Request data:", request_data)  # Debugging: Print request data
    
    # Extract user data and camera_id from the request
    user_id = request_data.get('user_id')
    email = request_data.get('email')
    camera_name= request_data.get('camera_name')
    
    if not camera_name or not user_id:
        return jsonify({'status': 'error', 'message': 'Camera ID or User ID missing'}), 400
    
    # Fetch the camera for the given user
    camera = db.cameras.find_one({"name": camera_name.strip(), "user_id": user_id}) 

    
    if not camera:
        return jsonify({'status': 'error', 'message': 'Camera not found for this user'}), 404



    # Add the alert to MongoDB
    alert_id = db.alerts.insert_one({
        'user_id': user_id,
        'timestamp': datetime.now(),
        'message': 'Fire alert triggered',
        'email': email,
        'camera_name': camera['name']
    }).inserted_id
    send_mail_function(email, camera['name'])

    return jsonify({'status': 'Alert added', 'alert_id': str(alert_id)})



def send_mail_function(recipientmail, camera_name=None):
    print(f"Preparing to send email to {recipientmail}")
    subject = "Fire Detection Alert"
    body = f"Warning: A fire accident has been reported by camera {camera_name}. Please check immediately." if camera_name else "Warning: A fire accident has been reported. Please check immediately."
    try:
        yag = yagmail.SMTP("your-email@gmail.com", 'your-app-password')  # Replace with correct credentials
        yag.send(to=recipientmail, subject=subject, contents=body)
        print(f"Email successfully sent to {recipientmail}")
    except Exception as e:
        print(f"Failed to send email to {recipientmail}. Error: {e}")

@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    user_id = session['user_id']
    alerts = list(db.alerts.find({'user_id': user_id}, {'_id': 1, 'timestamp': 1, 'message': 1.'camera_name':1}))
    for alert in alerts:
        alert['_id'] = str(alert['_id'])
    return jsonify(alerts)

def remove_alert(alert_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    user_id = session['user_id']
    result = db.alerts.delete_one({'_id': ObjectId(alert_id), 'user_id': user_id})

    if result.deleted_count == 0:
        return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

    return jsonify({'status': 'Alert removed successfully'})


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
    session.pop('user_id', None)  # Remove user ID from session
    session.pop('email', None) 
    flash('You have been logged out.', 'logout_success')
    return redirect(url_for('index'))


@app.route('/add_camera', methods=['POST'])
def add_camera():
    global ip_camera_url
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    data = request.form
    name = data.get('name')
    ip_address = data.get('ip_address')

    if not ip_address:
        return jsonify({'status': 'error', 'message': 'IP address is required'}), 400

    user_id = session['user_id']  # Get the user ID from the session
    ip_camera_url = ip_address

    # Store camera details in MongoDB associated with the user's ID
    camera_id = db.cameras.insert_one({
        'user_id': user_id,  # Associate the camera with the user
        'name': name,
        'ip_address': ip_address
    }).inserted_id

    # Respond to the client that the camera has been added successfully
    return jsonify({'status': 'Camera added successfully', 'camera_id': str(camera_id)})


@app.route('/remove_camera/<camera_id>', methods=['POST'])
def remove_camera(camera_id):
    global ip_camera_url
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    user_id = session['user_id']  # Get the user ID from the session

    # Remove camera details from MongoDB associated with the user's ID
    result = db.cameras.delete_one({'_id': ObjectId(camera_id), 'user_id': user_id})

    if result.deleted_count == 0:
        return jsonify({'status': 'error', 'message': 'Camera not found'}), 404

    # Reset the camera URL if the removed camera was the current one
    if ip_camera_url and ip_camera_url.endswith(camera_id):
        ip_camera_url = None

    return jsonify({'status': 'Camera removed successfully'})


@app.route('/get_cameras', methods=['GET'])
def get_cameras():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    user_id = session['user_id']

    cameras = list(db.cameras.find({'user_id': user_id}, {'_id': 1, 'name': 1, 'ip_address': 1}))
    for camera in cameras:
        camera['_id'] = str(camera['_id'])
    return jsonify(cameras)

@app.route('/get_camera_url', methods=['GET'])
def get_camera_url():
    return jsonify({'ip_camera_url': ip_camera_url})
