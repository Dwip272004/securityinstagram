import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import logging
from flask import Flask, request, jsonify
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')  # Log to a file for debugging
    ]
)

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG environment variable not set")
    
    # Parse and validate FIREBASE_CONFIG
    try:
        config_dict = json.loads(firebase_config)
        redacted_config = {k: v if k not in ['private_key', 'client_email', 'client_id'] else 'REDACTED' for k, v in config_dict.items()}
        logging.debug(f"FIREBASE_CONFIG content: {redacted_config}")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse FIREBASE_CONFIG: {str(e)}")
        raise ValueError(f"Invalid JSON in FIREBASE_CONFIG: {str(e)}")
    
    # Initialize Firebase
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
    logging.debug(f"Request: {request.method} {request.url} - Body: {request.get_json(silent=True)}")

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    """Returns a simple health check response."""
    return jsonify({"status": "ok", "message": "Server is running", "timestamp": datetime.utcnow().isoformat()}), 200

# Submit endpoint to add data to Firestore
@app.route('/submit', methods=['POST'])
def submit():
    """Handles POST requests to add data to the 'users' collection in Firestore."""
    try:
        # Validate request data
        data = request.get_json(silent=True)
        if not data:
            logging.warning("No JSON data provided in request")
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['name', 'email']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            logging.warning(f"Missing required fields: {missing_fields}")
            return jsonify({"status": "error", "message": f"Missing required fields: {missing_fields}"}), 400
        
        # Sanitize and enrich data
        sanitized_data = {
            'name': str(data['name']).strip(),
            'email': str(data['email']).strip(),
            'timestamp': datetime.utcnow().isoformat(),
            'id': str(uuid.uuid4())  # Add unique ID for each document
        }
        
        # Add data to Firestore
        db.collection('users').add(sanitized_data)
        logging.debug(f"Data added to Firestore: {sanitized_data}")
        return jsonify({"status": "success", "message": "Data added successfully", "data": sanitized_data}), 200
    except Exception as e:
        logging.error(f"Error in /submit: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Error handler for 400 Bad Request
@app.errorhandler(400)
def bad_request(error):
    """Handles 400 errors."""
    logging.warning(f"400 error: {str(error)}")
    return jsonify({"status": "error", "message": "Bad request"}), 400

# Error handler for 404 Not Found
@app.errorhandler(404)
def not_found(error):
    """Handles 404 errors."""
    logging.warning(f"404 error: {request.url}")
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

# Error handler for 405 Method Not Allowed
@app.errorhandler(405)
def method_not_allowed(error):
    """Handles 405 errors."""
    logging.warning(f"405 error: {request.method} {request.url}")
    return jsonify({"status": "error", "message": "Method not allowed"}), 405

# Error handler for 500 Internal Server Error
@app.errorhandler(500)
def internal_error(error):
    """Handles 500 errors."""
    logging.error(f"500 error: {str(error)}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    # Use the PORT environment variable provided by Render, default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
