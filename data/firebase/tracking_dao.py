from configs.config import MASHUPS_COLLECTION_NAME
from data.firebase.firestore_db import get_db
from datetime import datetime


class TrackingDao:
    def insert_mashup(self, msg_id: int, channel_id: int):
        now = datetime.now()
        doc_name = now.strftime("%m-%Y")  # Format: MM-YYYY (e.g., "02-2026")

        get_db().collection(MASHUPS_COLLECTION_NAME).document(doc_name).collection(str(msg_id)).document("info").set(
            {
                "channel_id": channel_id,
            },
        )

    def delete_mashup(self, msg_id: int):
        docs = get_db().collection_group(str(msg_id)).stream()

        for doc in docs:
            doc.reference.delete()
