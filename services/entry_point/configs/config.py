from dotenv import load_dotenv
import os
from firebase_admin import credentials
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv()

#server
HTTP_PORT = 3000
GENERATOR_PORT = 777
COMBINER_0_IP = "combiner"

APPLICATION_ID = 1428847584965034154

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
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
