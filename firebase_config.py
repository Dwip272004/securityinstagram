import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("logger-f9c87-firebase-adminsdk-fbsvc-26f12e5bb9.json")
firebase_admin.initialize_app(cred)
