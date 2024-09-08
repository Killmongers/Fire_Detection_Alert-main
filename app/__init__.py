from flask import Flask
from flask_pymongo import PyMongo
from .config import Config  # Import from the same directory

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from Config class

db= PyMongo(app).db  # Initialize PyMongo with Flask app

from . import routes  # Import routes after initializing the app
