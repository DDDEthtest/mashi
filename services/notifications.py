import firebase_admin
from firebase_admin import credentials, messaging
from configs.remote_config import FIREBASE_CRED_PATH, IOS_CRED_PATH

# Init
cred = credentials.Certificate(FIREBASE_CRED_PATH)
iosCred = credentials.Certificate(IOS_CRED_PATH)

app = firebase_admin.initialize_app(cred)                          # default app (Android)
ios = firebase_admin.initialize_app(iosCred, name="ios")           # ← named app required


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

        messaging.send(message, app=app)                           # ← pass app explicitly

    except Exception as e:
        print(e)


def notify_ios_users(title: str, body: str, listing_id=None):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={
                'listingId': str(listing_id) if listing_id else "",
            },
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    )
                )
            ),
            topic="ios_users"
        )

        messaging.send(message, app=ios)                           # ← ios app used here

    except Exception as e:
        print(e)