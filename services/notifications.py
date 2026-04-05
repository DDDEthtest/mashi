import firebase_admin
from firebase_admin import credentials, messaging
from configs.remote_config import FIREBASE_CRED_PATH

# Init
cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred)


def notify_android_users(title: str, body: str, listing_id=None):
    try:
        message = messaging.Message(
            data={
                'title': title,
                'body': body,
                'listingId': str(listing_id) if listing_id else "",
            },
            topic="all_users"
        )

        messaging.send(message)
    except Exception as e:
        print(e)
