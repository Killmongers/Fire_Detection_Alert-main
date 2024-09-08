from flask import Flask, Response, render_template, flash, redirect, session, url_for, request
from passlib.hash import pbkdf2_sha256
import uuid
from . import app, db  # Ensure you have a proper module import structure
from .fire_detection import gen_frames  # Ensure gen_frames is correctly imported
from werkzeug.security import generate_password_hash, check_password_hash  # Not used in this code snippet

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
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
    flash('You have been logged out.', 'logout_success')
    return redirect(url_for('index'))
