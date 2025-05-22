import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import logging
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if not firebase_config:
        raise ValueError("FIREBASE_CONFIG environment variable not set")
    
    # Attempt to parse the JSON string
    try:
        cred_dict = json.loads(firebase_config)
        logging.debug("FIREBASE_CONFIG parsed successfully")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse FIREBASE_CONFIG: {str(e)}")
        raise ValueError(f"Invalid JSON in FIREBASE_CONFIG: {str(e)}")
    
    # Initialize Firebase with the credentials
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.debug("Firebase initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Firebase: {str(e)}")
    raise

# Health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    """Returns a simple health check response."""
    return jsonify({"status": "ok", "message": "Server is running"}), 200

# Submit endpoint to add data to Firestore
@app.route('/submit', methods=['POST'])
def submit():
    """Handles POST requests to add data to the 'users' collection in Firestore."""
    try:
        # Validate request data
        data = request.json
        if not data:
            logging.warning("No JSON data provided in request")
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Add data to Firestore
        db.collection('users').add(data)
        logging.debug(f"Data added to Firestore: {data}")
        return jsonify({"status": "success", "message": "Data added successfully"}), 200
    except Exception as e:
        logging.error(f"Error in /submit: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    """Handles 404 errors."""
    logging.warning(f"404 error: {request.url}")
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

# Error handler for 500
@app.errorhandler(500)
def internal_error(error):
    """Handles 500 errors."""
    logging.error(f"500 error: {str(error)}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    # Use the PORT environment variable provided by Render, default to 5000 for local testing
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
