import logging
from api.client import api_client

logger = logging.getLogger(__name__)

def get_account_info():
    """Retrieves basic account info."""
    endpoint = "user/info/?fields=open_id,union_id,avatar_url,display_name"
    logger.info("Fetching account information.")
    
    response = api_client.get(endpoint)
    if "data" in response and "user" in response["data"]:
        user_data = response["data"]["user"]
        logger.info(f"Successfully retrieved info for user: {user_data.get('display_name')}")
        return user_data
    else:
        logger.error(f"Failed to fetch user info. Response: {response}")
        raise Exception("Failed to fetch user info.")
