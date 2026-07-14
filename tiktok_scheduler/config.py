import os
from dotenv import load_dotenv

load_dotenv()

TIKTOK_CLIENT_ID = os.getenv("TIKTOK_CLIENT_ID")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
# For local auth flow, we can use a local redirect URI
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8080/callback")

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")
SCHEDULE_FILE = os.path.join(DATA_DIR, "schedule.json")
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
ACTIVITY_FILE = os.path.join(DATA_DIR, "activity.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
