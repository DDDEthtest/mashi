from dotenv import load_dotenv
import os
from firebase_admin import credentials

from main import PROJECT_ROOT

load_dotenv()

#server
HTTP_PORT=80
HTTPS_PORT=443

#db
CRED_PATH = PROJECT_ROOT / "firebase_cred.json"
FIREBASE_CRED = credentials.Certificate(CRED_PATH)
COLLECTION_NAME = "discord-bot"

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

#channels
RELEASES_CHANNEL_ID = os.getenv("RELEASES_CHANNEL_ID")
TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID")

#roles
NEW_RELEASES_ROLE_ID = os.getenv("NEW_RELEASES_ROLE_ID")

#routes
NOTIFY_API_ROUTE = os.getenv("NOTIFY_API_ROUTE")

#apis
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#other:

#gif
MAX_GIF_GENERATIONS_AT_TIME = 4
GIF_MAKER_SERVER_URI = "http://localhost:3000"
ANIM_STEP = 0.03

#png
DEFAULT_PNG_WIDTH = 552 * 2
DEFAULT_PNG_HEIGHT = 736 * 2
DEFAULT_TRAIT_WIDTH = 380 * 2
DEFAULT_TRAIT_HEIGHT = 600 * 2