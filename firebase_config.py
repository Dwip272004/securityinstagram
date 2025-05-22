import firebase_admin
from firebase_admin import credentials, firestore

# Use the path where your secret file is mounted on Render
cred = credentials.Certificate('/etc/secrets/logger-f9c87-firebase-adminsdk-fbsvc-26f12e5bb9.json')

# Only initialize the app if it hasn’t been initialized already
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Export the Firestore client
db = firestore.client()
