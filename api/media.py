import os
import logging
import mimetypes
from api.client import api_client

logger = logging.getLogger(__name__)

def validate_file(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("The file is empty.")
    
    # Very basic validation, TikTok API has more specific constraints
    # (e.g., max 50MB for image, max 4GB for video, specific formats)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type or not (mime_type.startswith("image/") or mime_type.startswith("video/")):
        raise ValueError(f"Unsupported file format: {mime_type}")
        
    return file_size, mime_type

def upload_media(file_path: str):
    """
    Initializes upload and uploads the media file. 
    Note: TikTok uses a multi-step upload process for large files (Creator API or Direct Post API).
    This implements a basic direct upload approach based on common API patterns.
    Please consult specific API docs for chunked uploads if required.
    """
    logger.info(f"Starting upload for {file_path}")
    file_size, mime_type = validate_file(file_path)
    
    # The actual implementation of video/image upload depends on the specific 
    # TikTok Content Posting API endpoints.
    # Typically, you post to an init endpoint, then upload bytes, then commit.
    
    # 1. Initialize upload (Direct Post API flow)
    init_endpoint = "post/publish/video/init/"
    init_data = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1
        }
    }
    
    logger.info("Initializing media upload...")
    # NOTE: Since this is a PoC, we assume a simplified 1-step or direct approach.
    # The actual TikTok API may require chunking.
    try:
        init_response = api_client.post(init_endpoint, json=init_data)
        
        if "data" not in init_response or "upload_url" not in init_response["data"]:
            logger.error(f"Init upload failed: {init_response}")
            raise Exception("Failed to initialize upload.")
            
        upload_url = init_response["data"]["upload_url"]
        publish_id = init_response["data"].get("publish_id")
        
        # 2. Upload file bytes
        logger.info(f"Uploading bytes to {upload_url}...")
        with open(file_path, "rb") as f:
            # Note: Do not use api_client here as upload_url is usually an external S3/GCS link
            import requests
            upload_res = requests.put(upload_url, data=f, headers={"Content-Type": mime_type})
            upload_res.raise_for_status()
            
        logger.info(f"Upload complete. Publish ID: {publish_id}")
        return publish_id
    except Exception as e:
        logger.error(f"Error during media upload: {e}")
        raise
