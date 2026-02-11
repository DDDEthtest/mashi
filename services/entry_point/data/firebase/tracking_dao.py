import time

from configs.config import MASHUPS_COLLECTION_NAME
from data.firebase.firestore_db import get_db
from datetime import datetime


class TrackingDao:
    def insert_mashup(self, msg_id: int, channel_id: int):
        now = datetime.now()
        doc_name = now.strftime("%m-%Y") #Format: MM-YYYY (e.g., "02-2026")

        get_db().collection(MASHUPS_COLLECTION_NAME).document(doc_name).collection(str(msg_id)).document("info").set(
            {
                "channel_id": channel_id,
            },
        )

    def delete_mashup(self, msg_id: int):
        docs = get_db().collection_group(str(msg_id)).stream()

        for doc in docs:
            doc.reference.delete()

    # def _get_top_n_ranks(self, data_list, key_name, n=3):
    #     """Helper to get all items belonging to the top N unique scores."""
    #     if not data_list:
    #         return []
    #
    #     # 1. Get unique scores in descending order
    #     unique_scores = sorted(list(set(item[key_name] for item in data_list)), reverse=True)
    #
    #     # 2. Take the top N scores
    #     top_n_scores = unique_scores[:n]
    #
    #     # 3. Filter list to include anyone with those scores and sort them
    #     winners = [item for item in data_list if item[key_name] in top_n_scores]
    #     return sorted(winners, key=lambda x: x[key_name], reverse=True)
    #
    # def get_monthly_top(self):
    #     db = get_db()
    #     docs = db.collection(TRACKING_COLLECTION_NAME).stream()
    #
    #     user_scores = defaultdict(int)
    #     post_stats = []
    #
    #     for doc in docs:
    #         data = doc.to_dict()
    #         poster_id = data.get("poster")
    #
    #         # Count subcollections (each represents a unique user interaction)
    #         sub_count = len(list(doc.reference.collections()))
    #
    #         # Return msg_id as int
    #         post_stats.append({"msg_id": int(doc.id), "count": sub_count})
    #
    #         if poster_id:
    #             # poster_id is already an int from the DB
    #             user_scores[poster_id] += sub_count
    #
    #     # Convert user_scores dict to list for ranking
    #     user_list = [{"poster_id": k, "total_count": v} for k, v in user_scores.items()]
    #
    #     return {
    #         "top_posts": self._get_top_n_ranks(post_stats, "count", 3),
    #         "top_users": self._get_top_n_ranks(user_list, "total_count", 3)
    #     }
    #
    # def delete_post_tracking(self, msg_id: int):
    #     """Deletes a specific message document and all its user subcollections."""
    #     db = get_db()
    #     s_msg_id = str(msg_id)
    #
    #     # 1. Get the reference to the parent document
    #     doc_ref = db.collection(TRACKING_COLLECTION_NAME).document(s_msg_id)
    #
    #     # 2. Iterate through and delete all subcollections (user_id collections)
    #     subcollections = doc_ref.collections()
    #     for sub in subcollections:
    #         # Delete every document inside the subcollection (e.g., 'init')
    #         for sub_doc in sub.stream():
    #             sub_doc.reference.delete()
    #
    #     # 3. Finally, delete the parent message document
    #     doc_ref.delete()
    #
    # def clear_tracking(self):
    #     """Deletes all data within the tracking collection."""
    #     db = get_db()
    #     docs = db.collection(TRACKING_COLLECTION_NAME).stream()
    #
    #     for doc in docs:
    #         # Must delete subcollections first to avoid 'orphan' data
    #         subcollections = doc.reference.collections()
    #         for sub in subcollections:
    #             for sub_doc in sub.stream():
    #                 sub_doc.reference.delete()
    #
    #         # Delete the parent message document
    #         doc.reference.delete()
