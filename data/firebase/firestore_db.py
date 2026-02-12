import firebase_admin
from firebase_admin import firestore
from configs.config import FIREBASE_CRED


class FirestoreDB:
    _instance = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_firebase()
        return cls._instance

    def _init_firebase(self):
        firebase_admin.initialize_app(FIREBASE_CRED)
        self._db = firestore.client()

    def get_db(self):
        return self._db


def get_db():
    return FirestoreDB().get_db()
