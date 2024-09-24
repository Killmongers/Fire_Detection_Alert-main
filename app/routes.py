from flask import Flask, Response, render_template, flash, redirect, session, url_for, request, jsonify
from passlib.hash import pbkdf2_sha256
import uuid
from . import app, db  # Ensure you have a proper module import structure
from bson.objectid import ObjectId
from bson.errors import InvalidId
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





@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = db.users.find_one({'_id': session['user_id']})
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', user.get('name', ''))
        surname = request.form.get('surname', user.get('surname', ''))
        username = request.form.get('username', user.get('username', ''))
        mobile = request.form.get('mobile', user.get('mobile', ''))
        address = request.form.get('address', user.get('address', ''))
        postcode = request.form.get('postcode', user.get('postcode', ''))
        state = request.form.get('state', user.get('state', ''))
        area = request.form.get('area', user.get('area', ''))
        email = request.form.get('email', user.get('email', ''))

        # Prepare update data
        update_data = {}
        if name != user.get('name', ''):
            update_data['name'] = name
        if surname != user.get('surname', ''):
            update_data['surname'] = surname
        if username != user.get('username', ''):
            update_data['username'] = username
        if mobile != user.get('mobile', ''):
            update_data['mobile'] = mobile
        if address != user.get('address', ''):
            update_data['address'] = address
        if postcode != user.get('postcode', ''):
            update_data['postcode'] = postcode
        if state != user.get('state', ''):
            update_data['state'] = state
        if area != user.get('area', ''):
            update_data['area'] = area
        if email != user.get('email', ''):
            update_data['email'] = email

        # Only update if there's something to change
        if update_data:
            db.users.update_one(
                {'_id': session['user_id']},
                {'$set': update_data}
            )

        # Optionally, redirect or flash a success message
        return redirect(url_for('profile'))

    return render_template('dashboard.html', 
                           name=user.get('name', ''),
                           surname=user.get('surname', ''),
                           username=user.get('username', ''),
                           email=user.get('email', ''),
                           mobile=user.get('mobile', ''),
                           address=user.get('address', ''),
                           postcode=user.get('postcode', ''),
                           state=user.get('state', ''),
                           area=user.get('area', ''))




@app.route('/home')
def home():
    
    
    if 'username' in session and 'email' in session:
        return render_template('home.html', username=session['username'])
    
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = db.users.find_one({'email': email})
        if user and pbkdf2_sha256.verify(password, user['password']):
            session['username'] = user['username']
            session['user_id'] = str(user['_id'])  # Ensure user ID is converted to string
            session['email'] = user['email']
            session['is_admin'] = user.get('is_admin', False)  # Store admin status in session

            flash('Login successful!', 'login_success')

            # Redirect to admin dashboard if user is an admin
            if session['is_admin']:
                return redirect(url_for('admin_dashboard'))

            return redirect(url_for('home'))  # Regular user redirection

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
    alerts = list(db.alerts.find({'user_id': user_id}, {'_id': 1, 'timestamp': 1, 'message': 1,'camera_name':1}))
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


authorized_admins = ['admin@example.com']  # Update this list with actual admin emails

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'

        # Restrict admin designation to authorized users
        if email not in authorized_admins:
            is_admin = False  # Forbid normal users from signing up as admins

        if not username or not email or not phone or not password:
            
            return redirect(url_for('signup'),flash('All fields are required!', 'signup_error'))

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
            "password": hashed_password,
            "is_admin": is_admin  # Store admin designation
        }

        db.users.insert_one(new_user)
        flash('Signup successful! You can now log in.', 'signup_success')
        return redirect(url_for('login'))

    return redirect(url_for('signup'))


@app.route('/logout',methods=['POST','GET'])
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




@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    return render_template('admin_dashboard.html')


# Admin users list
@app.route('/admin_users')
def admin_users():
    users = list(db.users.find({}, {'_id': 1, 'username': 1, 'email': 1, 'is_admin': 1}))
    for user in users:
        user['_id'] = str(user['_id'])
    return render_template('admin_users.html', users=users)
    

@app.route('/admin_cameras')
def admin_cameras():
    # Retrieve all cameras from the database
    cameras = list(db.cameras.find({}, {'_id': 1, 'user_id': 1, 'name': 1, 'ip_address': 1}))

    # Fetch user data for each camera
    for camera in cameras:
        user = db.users.find_one({'_id': camera['user_id']}, {'username': 1})  # Fetch the user's username
        camera['owner_username'] = user['username'] if user else 'Unknown'  # Add username to the camera details

    # Pass the cameras (with owner info) to the template
    return render_template('admin_cameras.html', cameras=cameras)


@app.route('/admin_alerts')
def admin_alerts():
    # Fetch all alerts for admin to review
    alerts = list(db.alerts.find({}, {'_id': 1, 'timestamp': 1, 'user_id':1,'message': 1, 'camera_name': 1, 'email': 1}).sort('timestamp', -1))
    for alert in alerts:
        user = db.users.find_one({'_id': alert['user_id']}, {'username': 1}) 
        alert['owner_username'] = user['username'] if user else 'Unknown' 
        alert['_id'] = str(alert['_id'])
    return render_template('admin_alerts.html', alerts=alerts)




@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        # Convert user_id to ObjectId
        user_object_id = user_id

        # Attempt to delete the user
        result = db.users.delete_one({'_id': user_object_id})

        if result.deleted_count > 0:
            flash('User deleted successfully!', 'success')
        else:
            flash('User not found.', 'error')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')

    return redirect(url_for('admin_users'))


@app.route('/delete_camera/<camera_id>', methods=['POST'])
def delete_camera(camera_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    result = db.cameras.delete_one({'_id': ObjectId(camera_id)})
    if result.deleted_count == 0:
        return jsonify({'status': 'error', 'message': 'Camera not found'}), 404

    flash(f'Camera {camera_id} deleted successfully!', 'delete_success')
    return redirect(url_for('admin_cameras'))


@app.route('/delete_alert/<alert_id>', methods=['POST'])
def delete_alert(alert_id):
    if 'is_admin' not in session or not session['is_admin']:
        return jsonify({'status': 'error', 'message': 'Unauthorized access'}), 403

    result = db.alerts.delete_one({'_id': ObjectId(alert_id)})
    if result.deleted_count == 0:
        return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

    flash(f'Alert {alert_id} deleted successfully!', 'delete_success')
    return redirect(url_for('admin_alerts'))



from bson.objectid import ObjectId

@app.route('/update_camera/<camera_id>', methods=['POST'])
def update_camera(camera_id):
    
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    name = request.form.get('name')
    ip_address = request.form.get('ip_address')

    # Ensure both fields are provided
    if not name or not ip_address:
        flash('Camera name and IP address are required.', 'update_error')
        return redirect(url_for('admin_cameras'))

    # Convert camera_id to ObjectId and update the camera details in MongoDB
    try:
        result = db.cameras.update_one(
            {'_id': ObjectId(camera_id)},  # Convert camera_id to ObjectId
            {'$set': {'name': name, 'ip_address': ip_address}}
        )
    except Exception as e:
        flash(f'Error updating camera: {str(e)}', 'update_error')
        return redirect(url_for('admin_cameras'))

    if result.matched_count == 0:
        flash('Camera not found or unauthorized access.', 'update_error')
        return redirect(url_for('admin_cameras'))

    flash('Camera updated successfully!', 'update_success')
    return redirect(url_for('admin_cameras'))


@app.route('/show_user/<user_id>', methods=['GET'])
def show_user(user_id):
    try:
        user = db.users.find_one({'_id': user_id})
    except InvalidId:
        flash('Invalid user ID format.', 'error')
        return redirect(url_for('admin_users'))
    except Exception as e:
        flash('Error retrieving user.', 'error')
        return redirect(url_for('admin_users'))

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    # Convert ObjectId to string for rendering
    user['_id'] = str(user['_id'])

    return render_template('show_user.html', user=user)

@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
   
    if 'is_admin' not in session or not session['is_admin']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('admin_users'))  # Redirect to admin users page

    try:
        user = db.users.find_one({'_id': user_id})
    except Exception as e:
        flash('Error retrieving user.', 'error')
        return redirect(url_for('admin_users'))

    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        is_admin = request.form.get('is_admin') == 'on'
        new_password = request.form.get('password')

        # Prepare data for update
        update_data = {'is_admin': is_admin}
        
        # Update password if a new one is provided
        if new_password:
            hashed_password = pbkdf2_sha256.hash(new_password)
            update_data['password'] = hashed_password

        db.users.update_one({'_id': user_id}, {'$set': update_data})

        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    # Render the edit form
    return render_template('edit_user.html', user=user)
