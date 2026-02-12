from configs.config import COLLECTION_NAME
from data.firebase.firestore_db import get_db


class ReactionsDao:
    def update_reaction_count(self, user_id: int, amount: int):
        db = get_db()
        user_ref = db.collection(COLLECTION_NAME).document(str(user_id))

        # 1. Manually get the document
        doc = user_ref.get()

        current_count = 0
        if doc.exists:
            # Get the field, default to 0 if it's missing
            current_count = doc.to_dict().get("reaction_count", 0)

        # 2. Update it manually
        user_ref.set({
            "reaction_count": max(0, current_count + amount)
        }, merge=True)

    def get_reaction_count(self, user_id: int) -> int:
        doc = get_db().collection(COLLECTION_NAME).document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict().get("reaction_count", 0)
        return 0

    def get_user_position(self, user_id: int) -> int | None:
        db = get_db()
        # 1. Get the target user's current count
        user_doc = db.collection(COLLECTION_NAME).document(str(user_id)).get()

        if not user_doc.exists:
            return None

        user_data = user_doc.to_dict()
        user_count = user_data.get("reaction_count", 0)

        # 2. Count how many users have a higher count
        # We use count() here which is more efficient than fetching all documents
        query = (
            db.collection(COLLECTION_NAME)
            .where("reaction_count", ">", user_count)
            .count()
        )

        results = query.get()
        # Position is (count of people above) + 1
        return results[0][0].value + 1

    def get_reaction_leaderboard(self, limit: int = 10, offset: int = 0) -> list[dict]:
        # Added .offset(offset) to the query chain
        docs = (
            get_db()
            .collection(COLLECTION_NAME)
            .order_by("reaction_count", direction="DESCENDING")
            .limit(limit)
            .offset(offset)
            .stream()
        )

        leaderboard = []
        for doc in docs:
            data = doc.to_dict()
            leaderboard.append({
                "user_id": doc.id,
                "reaction_count": data.get("reaction_count", 0)
            })

        return leaderboard
