from dotenv import load_dotenv
import os
from firebase_admin import credentials
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv()

#server
HTTP_PORT=3000
GIF_LOCAL_SERVER_PORT = 3001

#db
CRED_PATH = PROJECT_ROOT / os.getenv("FIREBASE_CRED_FILE_NAME")
FIREBASE_CRED = credentials.Certificate(CRED_PATH)
COLLECTION_NAME = "discord-bot"

#channels
RELEASES_CHANNEL_ID = os.getenv("RELEASES_CHANNEL_ID")
TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID")

#roles
NEW_RELEASES_ROLE_ID = os.getenv("NEW_RELEASES_ROLE_ID")

#apis
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#other:

#gif
MAX_GIF_GENERATIONS_AT_TIME = 3
GIF_MAKER_SERVER_URI = f"http://localhost:{GIF_LOCAL_SERVER_PORT}"
ANIM_STEP = 0.03

#png
DEFAULT_PNG_WIDTH = 552 * 2
DEFAULT_PNG_HEIGHT = 736 * 2
DEFAULT_TRAIT_WIDTH = 380 * 2
DEFAULT_TRAIT_HEIGHT = 600 * 2