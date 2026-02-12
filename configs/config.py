from pathlib import Path

from dotenv import load_dotenv
import os
from firebase_admin import credentials

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent

# server
HTTP_PORT = 3000
GIF_MAKER_SERVER_PORT = 666
GIF_MAKER_SERVER_URI = f"http://localhost:{GIF_MAKER_SERVER_PORT}"

# app
APPLICATION_ID = 1428847584965034154

# channels
RELEASES_CHANNEL_ID = 1419703216979054653
TEST_CHANNEL_ID = 1428716774035030109

# roles
NEW_RELEASES_ROLE_ID = 1420043943319437312

# apis
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
