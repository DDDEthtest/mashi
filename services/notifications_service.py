import firebase_admin
from firebase_admin import credentials, messaging

from configs.config import FIREBASE_CRED_PATH

cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred)

def notify_android_users(title, body, listing_id=None):
    # 2. Define the message
    message = messaging.Message(
        # Remove the notification=... block entirely
        data={
            'title': title,
            'body': body,
            'listingId': str(listing_id) if listing_id else "",
        },
        topic="all_users", # This targets everyone subscribed
    )

    # 3. Send the message
    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
    except Exception as e:
        print(f"Error sending message: {e}")