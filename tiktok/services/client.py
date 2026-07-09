import logging
import requests
from tiktok.services.token_manager import get_tokens
import time

logger = logging.getLogger(__name__)

class TikTokAPIClient:
    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self):
        self.session = requests.Session()

    def _get_headers(self, requires_auth=True, content_type="application/json"):
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
            
        if requires_auth:
            tokens = get_tokens()
            if tokens and tokens.get("access_token"):
                headers["Authorization"] = f"Bearer {tokens['access_token']}"
            else:
                logger.error("Missing access token for API request.")
                raise ValueError("Authentication required but no access token available.")
        return headers

    def _request(self, method, endpoint, requires_auth=True, **kwargs):
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        headers = kwargs.pop('headers', {})
        default_headers = self._get_headers(requires_auth, content_type=kwargs.pop('content_type', "application/json"))
        headers.update(default_headers)
        
        # Strip content-type if None to allow requests to calculate it (e.g. multipart/form-data)
        if "Content-Type" in headers and headers["Content-Type"] is None:
            del headers["Content-Type"]
            
        logger.info(f"API Request: {method} {url}")
        
        # Basic retry logic for 429 Too Many Requests
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
                logger.error(f"Network or API Error during {method} {url}: {str(e)}")
                raise

        raise Exception("Max retries exceeded for API request.")

    def get(self, endpoint, **kwargs):
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._request("POST", endpoint, **kwargs)

api_client = TikTokAPIClient()
