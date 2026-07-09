import urllib.parse
import logging
from config import config
from api.client import api_client
from storage.token_manager import save_tokens, update_tokens, get_tokens
import requests

logger = logging.getLogger(__name__)

def get_auth_url():
    """Generates the authorization URL for the user to log in."""
    base_url = "https://www.tiktok.com/v2/auth/authorize/"
    scopes = ["user.info.basic", "video.upload"]
    
    params = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "response_type": "code",
        "scope": ",".join(scopes),
        "redirect_uri": config.REDIRECT_URI,
        "state": "tiktok_scheduler_poc"
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    logger.info("Generated TikTok Auth URL.")
    return url

def fetch_tokens(auth_code: str):
    """Exchanges the authorization code for an access token."""
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    
    data = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "client_secret": config.TIKTOK_CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": config.REDIRECT_URI
    }
    
    logger.info("Fetching tokens with auth code.")
    response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    response.raise_for_status()
    
    resp_data = response.json()
    if "data" in resp_data and "access_token" in resp_data["data"]:
        token_data = resp_data["data"]
        save_tokens(token_data["access_token"], token_data["refresh_token"], token_data.get("expires_in"))
        logger.info("Successfully fetched and saved tokens.")
        return token_data
    else:
        logger.error(f"Failed to fetch tokens. Response: {resp_data}")
        raise Exception("Failed to fetch tokens from TikTok.")

def refresh_access_token():
    """Refreshes the access token using the stored refresh token."""
    tokens = get_tokens()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        logger.error("No refresh token available.")
        raise ValueError("No refresh token available. User must log in again.")
        
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    
    data = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "client_secret": config.TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    logger.info("Refreshing access token.")
    response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    response.raise_for_status()
    
    resp_data = response.json()
    if "data" in resp_data and "access_token" in resp_data["data"]:
        token_data = resp_data["data"]
        update_tokens(token_data["access_token"], token_data["refresh_token"])
        logger.info("Successfully refreshed access token.")
        return token_data
    else:
        logger.error(f"Failed to refresh tokens. Response: {resp_data}")
        raise Exception("Failed to refresh tokens from TikTok.")
