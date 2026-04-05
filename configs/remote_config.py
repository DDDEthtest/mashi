import os
from pathlib import Path
from dotenv import load_dotenv

# Env
load_dotenv()
PROJECT_ROOT = Path(__file__).parent.parent

# Remote
MASHIT_KEY = os.getenv("MASHIT_KEY")
MASHIT_BASE_URL = "https://avatar-artists-guild.web.app/"

# Firebase
FIREBASE_CRED_NAME = os.getenv("FIREBASE_CRED_NAME")
FIREBASE_CRED_PATH = PROJECT_ROOT / FIREBASE_CRED_NAME
