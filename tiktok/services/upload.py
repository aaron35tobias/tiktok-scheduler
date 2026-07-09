import os
import shutil
import uuid
import logging
from .client import api_client
from django.conf import settings

logger = logging.getLogger(__name__)

REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", os.getenv("REDIRECT_URI", ""))
# Extract the base host from redirect URI (e.g. https://xyz.ngrok-free.dev)
# If not available, fallback to a generic localhost for local testing
import urllib.parse
parsed_uri = urllib.parse.urlparse(REDIRECT_URI)
BASE_HOST = f"{parsed_uri.scheme}://{parsed_uri.netloc}" if parsed_uri.netloc else "http://localhost:8000"

def upload_media(file_path: str, caption: str = "") -> str:
    """
    Initializes and uploads media to TikTok APIs.
    For photos, copies the file to Django MEDIA_ROOT to serve it publicly via Ngrok,
    then uses PULL_FROM_URL.
    For videos, uses FILE_UPLOAD direct upload.
    Returns the publish_id.
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
        
    file_size = os.path.getsize(file_path)
    
    if mime_type.startswith("image/"):
        logger.info("Photo detected. Preparing to serve via Django MEDIA_URL for PULL_FROM_URL...")
        
        # Copy file to media directory
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        ext = os.path.splitext(file_path)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        media_dest = os.path.join(settings.MEDIA_ROOT, unique_filename)
        shutil.copy2(file_path, media_dest)
        
        # Construct public URL using the base host from TIKTOK_REDIRECT_URI
        public_url = f"{BASE_HOST}{settings.MEDIA_URL}{unique_filename}"
        logger.info(f"Generated public URL for photo: {public_url}")
        
        init_endpoint = "post/publish/content/init/"
        init_data = {
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_images": [public_url]
            },
            "post_info": {
                "title": caption if caption else "Photo Upload",
                "privacy_level": "SELF_ONLY"
            }
        }
    else:
        init_endpoint = "post/publish/video/init/"
        init_data = {
            "post_mode": "DIRECT_POST",
            "media_type": "VIDEO",
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            },
            "post_info": {
                "title": caption if caption else "Video Upload",
                "privacy_level": "SELF_ONLY"
            }
        }
        
    try:
        init_response = api_client.post(init_endpoint, json=init_data)
        
        if "data" not in init_response:
            logger.error(f"Init upload failed: {init_response}")
            raise Exception("Failed to initialize upload.")
            
        data = init_response["data"]
        upload_url = data.get("upload_url")
        publish_id = data.get("publish_id")
        
        if upload_url:
            # 2. Upload file bytes (for VIDEO)
            logger.info(f"Uploading bytes to {upload_url}...")
            with open(file_path, "rb") as f:
                import requests
                upload_res = requests.put(upload_url, data=f, headers={"Content-Type": mime_type})
                upload_res.raise_for_status()
                
            logger.info(f"Upload complete. Publish ID: {publish_id}")
        else:
            if not publish_id:
                logger.error(f"Init upload failed (missing upload_url and publish_id): {init_response}")
                raise Exception("Failed to find upload_url in response.")
            logger.info(f"Photo pulled directly by TikTok. Publish ID: {publish_id}")
            
        return publish_id
    except Exception as e:
        logger.error(f"Error during media upload: {e}")
        raise
