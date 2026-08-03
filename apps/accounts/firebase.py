import firebase_admin

from firebase_admin import credentials

from django.conf import settings

import os


firebase_app = None


def initialize_firebase():

    global firebase_app

    if firebase_admin._apps:
        firebase_app = firebase_admin.get_app()
        return firebase_app

    credential_path = os.path.join(
        settings.BASE_DIR,
        settings.FIREBASE_CREDENTIALS,
    )

    if not os.path.exists(credential_path):
        print("Warning: Firebase credentials not found at", credential_path)
        return None

    try:
        cred = credentials.Certificate(credential_path)
        firebase_app = firebase_admin.initialize_app(cred)
    except Exception as e:
        print("Failed to initialize Firebase:", e)
        return None

    return firebase_app