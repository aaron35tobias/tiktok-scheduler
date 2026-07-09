import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    TIKTOK_CLIENT_ID = os.getenv("TIKTOK_CLIENT_ID")
    TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tiktok_scheduler.db")
    TIMEZONE = os.getenv("TIMEZONE", "UTC")
    
    # Store token info in the database or simply load from env for POC
    # If we manage tokens dynamically, these are just initial fallbacks
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

config = Config()
