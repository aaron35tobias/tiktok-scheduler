import logging
from .client import api_client

logger = logging.getLogger(__name__)

def publish_post(publish_id: str, caption: str = "", privacy_level: str = "SELF_ONLY", disable_comment: bool = False, disable_duet: bool = False, disable_stitch: bool = False):
    """
    Commits the published video/image.
    """
    logger.info(f"Publishing post with ID: {publish_id}")
    endpoint = "post/publish/video/commit/"
    
    data = {
        "publish_id": publish_id,
        "post_info": {
            "title": caption,
            "privacy_level": privacy_level,
            "disable_comment": disable_comment,
            "disable_duet": disable_duet,
            "disable_stitch": disable_stitch
        }
    }
    
    response = api_client.post(endpoint, json=data)
    logger.info(f"Publish response: {response}")
    
    if "error" in response and response["error"]["code"] != "ok":
        logger.error(f"Failed to publish post: {response}")
        raise Exception(f"Publish failed: {response['error'].get('message', 'Unknown error')}")
        
    return response

def get_post_status(publish_id: str):
    """
    Checks the status of a post if it's processing.
    """
    logger.info(f"Checking status for post ID: {publish_id}")
    endpoint = "post/publish/status/fetch/"
    data = {
        "publish_id": publish_id
    }
    
    response = api_client.post(endpoint, json=data)
    if "data" in response and "status" in response["data"]:
        return response["data"]["status"]
    
    raise Exception(f"Failed to get status. Response: {response}")
