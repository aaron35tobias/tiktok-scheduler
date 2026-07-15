import logging
import requests
import time
from typing import Optional, Dict, Any
from .storage import Storage
from . import config

logger = logging.getLogger(__name__)

class TikTokAPIClient:
    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self):
        self.session = requests.Session()

    def _get_headers(self, requires_auth=True, content_type="application/json", access_token=None) -> Dict[str, str]:
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        if requires_auth:
            # Prefer an explicitly provided token (e.g. the post's owning account),
            # otherwise fall back to the active account's stored token.
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            else:
                token = Storage.load_tokens()
                if token and token.access_token:
                    headers["Authorization"] = f"Bearer {token.access_token}"
                else:
                    logger.error("Missing access token for API request.")
                    raise ValueError("Authentication required but no access token available.")
        return headers

    def refresh_token(self):
        token = Storage.load_tokens()
        if not token or not token.refresh_token:
            logger.error("No refresh token available.")
            raise ValueError("No refresh token available. User must log in again.")
            
        url = "https://open.tiktokapis.com/v2/oauth/token/"
        data = {
            "client_key": config.TIKTOK_CLIENT_ID,
            "client_secret": config.TIKTOK_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token
        }
        
        logger.info("Refreshing access token.")
        response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        response.raise_for_status()
        
        resp_data = response.json()
        token_data = resp_data.get("data", resp_data)
        
        if "access_token" in token_data:
            token.access_token = token_data["access_token"]
            if token_data.get("refresh_token"):
                token.refresh_token = token_data["refresh_token"]
            token.expires_at = time.time() + token_data.get("expires_in", 86400)
            Storage.save_tokens(token)
            logger.info("Successfully refreshed access token.")
        else:
            logger.error(f"Failed to refresh tokens. Response: {resp_data}")
            raise Exception("Failed to refresh tokens from TikTok.")

    def _request(self, method: str, endpoint: str, requires_auth=True, **kwargs) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        access_token = kwargs.pop('access_token', None)
        headers = kwargs.pop('headers', {})
        default_headers = self._get_headers(requires_auth, content_type=kwargs.pop('content_type', "application/json"), access_token=access_token)
        headers.update(default_headers)
        
        # Strip content-type if None to allow requests to calculate it
        if "Content-Type" in headers and headers["Content-Type"] is None:
            del headers["Content-Type"]
            
        logger.info(f"API Request: {method} {url}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, headers=headers, **kwargs)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                error_msg = f"Network or API Error during {method} {url}: {str(e)}"
                if getattr(e, 'response', None) is not None:
                    error_msg += f" - Response body: {e.response.text}"
                logger.error(error_msg)
                
                # If we get a 401 Unauthorized, we might need to refresh the token and retry
                if getattr(e, 'response', None) is not None and e.response.status_code == 401 and attempt == 0:
                    logger.info("Attempting token refresh due to 401 response...")
                    try:
                        self.refresh_token()
                        # Update headers with new token
                        headers.update(self._get_headers(requires_auth, content_type=headers.get("Content-Type")))
                        continue
                    except Exception as refresh_err:
                        logger.error(f"Token refresh failed: {refresh_err}")
                
                raise

        raise Exception("Max retries exceeded for API request.")

    def get(self, endpoint: str, **kwargs):
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs):
        return self._request("POST", endpoint, **kwargs)

    def get_user_info(self) -> Dict[str, Any]:
        """Fetches the connected user's profile. Requires user.info.basic
        (+ user.info.profile / user.info.stats for the fuller fields).
        Falls back to just basic fields if the fuller request is rejected."""
        full_fields = (
            "open_id,union_id,avatar_url,display_name,username,"
            "follower_count,following_count,likes_count,video_count,is_verified"
        )
        basic_fields = "open_id,union_id,avatar_url,display_name"
        try:
            resp = self.get(f"user/info/?fields={full_fields}")
        except Exception as e:
            logger.warning(f"Full user.info fetch failed ({e}); retrying with basic fields.")
            resp = self.get(f"user/info/?fields={basic_fields}")
        return resp.get("data", {}).get("user", {})

api_client = TikTokAPIClient()
