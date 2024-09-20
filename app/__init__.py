from flask import Flask, session
from flask_pymongo import PyMongo
from .config import Config
from flask_session import Session
from datetime import timedelta



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_here'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=16)

app.config.from_object(Config)  # Load configuration from Config class

db= PyMongo(app).db  # Initialize PyMongo with Flask app 
from . import routes  # Import routes after initializing the app and  config .py import os
