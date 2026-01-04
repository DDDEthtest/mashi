from configs.config import COLLECTION_NAME
from data.firebase.firebase_db import get_db


class MashersDao:
    def connect_wallet(self, user_id: int, wallet: str):
        get_db().collection(COLLECTION_NAME).document(str(user_id)).set({
            "wallet": wallet,
        })

    def disconnect_wallet(self, user_id: int):
        get_db().collection(COLLECTION_NAME).document(str(user_id)).delete()

    def get_wallet(self, user_id: int) -> str | None:
        doc = get_db().collection(COLLECTION_NAME).document(str(user_id)).get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("wallet")  # returns the wallet string
        return None  # document or wallet field does not exist

    def check_if_wallet_taken(self, wallet: str) -> bool:
        query = get_db().collection(COLLECTION_NAME).where("wallet", "==", wallet).limit(1)
        results = query.get()
        if results:
            return True
        return False
