import os
import firebase_admin
from firebase_admin import credentials

# Example: Render mounts secret to /etc/secrets/firebase.json
cred_path = "/etc/secrets/logger-f9c87-firebase-adminsdk-fbsvc-26f12e5bb9.json"  # Change to your mounted secret path
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
