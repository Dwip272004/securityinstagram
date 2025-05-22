import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize Firebase Admin SDK
try:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG environment variable not set")
    
    try:
        config_dict = json.loads(firebase_config)
        redacted_config = {k: v if k not in ['private_key', 'client_email', 'client_id'] else 'REDACTED' for k, v in config_dict.items()}
        logging.debug(f"FIREBASE_CONFIG content: {redacted_config}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse FIREBASE_CONFIG: {str(e)}")
        raise ValueError(f"Invalid JSON in FIREBASE_CONFIG: {str(e)}")
    
    cred = credentials.Certificate(config_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.debug("Firebase initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Firebase: {str(e)}")
    raise

# Middleware to log incoming requests
@app.before_request
def log_request_info():
    """Log details of incoming requests."""
    logging.debug(f"Request: {request.method} {request.url} - Form: {request.form} - JSON: {request.get_json(silent=True)} - Headers: {dict(request.headers)}")

# Root endpoint to render login page
@app.route('/', methods=['GET'])
def login_page():
    """Renders the login page."""
    return render_template('login.html', error=None)

# Login endpoint to handle form submissions
@app.route('/login', methods=['POST'])
def login():
    """Handles login form submissions."""
    try:
        # Log the entire request for debugging
        logging.debug(f"Login request - Form data: {request.form}")
        
        # Get form data
        email = request.form.get('email')
        name = request.form.get('name')
        
        if not request.form:
            logging.warning("No form data received in /login")
            return render_template('login.html', error="No form data provided")
        
        if not email:
            logging.warning("Email not provided in login form")
            return render_template('login.html', error="Email is required")
        
        # Store user data in Firestore
        user_data = {
            'email': email.strip(),
            'name': name.strip() if name else '',
            'timestamp': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4())
        }
        db.collection('users').add(user_data)
        logging.debug(f"User data added to Firestore: {user_data}")
        
        # Redirect to dashboard
        return redirect(url_for('dashboard', email=user_data['email']))
    except Exception as e:
        logging.error(f"Error in /login: {str(e)}")
        return render_template('login.html', error=str(e))

# Dashboard endpoint after successful login
@app.route('/dashboard')
def dashboard():
    """Renders the dashboard page after login."""
    email = request.args.get('email', 'Guest')
    return render_template('dashboard.html', email=email)

# Submit endpoint for API-based data submission
@app.route('/submit', methods=['POST'])
def submit():
    """Handles POST requests to add data to the 'users' collection in Firestore."""
    try:
        data = request.get_json(silent=True)
        if not data:
            logging.warning("No JSON data provided in request")
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        required_fields = ['name', 'email']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            logging.warning(f"Missing required fields: {missing_fields}")
            return jsonify({"status": "error", "message": f"Missing required fields: {missing_fields}"}), 400
        
        sanitized_data = {
            'name': str(data['name']).strip(),
            'email': str(data['email']).strip(),
            'timestamp': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4())
        }
        
        db.collection('users').add(sanitized_data)
        logging.debug(f"Data added to Firestore: {sanitized_data}")
        return jsonify({"status": "success", "message": "Data added successfully", "data": sanitized_data}), 200
    except Exception as e:
        logging.error(f"Error in /submit: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    logging.warning(f"400 error: {str(error)}")
    return jsonify({"status": "error", "message": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    logging.warning(f"404 error: {request.url}")
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    logging.warning(f"405 error: {request.method} {request.url}")
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"500 error: {str(error)}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
