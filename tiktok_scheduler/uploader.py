import os
import math
import mimetypes
import logging
import requests
from .api import api_client

logger = logging.getLogger(__name__)

class TikTokUploader:
    def upload_media(self, file_path: str, caption: str = "",
                     privacy_level: str = "SELF_ONLY",
                     disable_comment: bool = False,
                     disable_duet: bool = False,
                     disable_stitch: bool = False) -> str:
        """
        Initializes and uploads media to TikTok APIs.
        Returns the publish_id.
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        file_size = os.path.getsize(file_path)

        # TikTok requires each upload chunk to be between 5MB and 64MB.
        # Small videos go up in one chunk; large ones are split into equal chunks.
        MAX_CHUNK = 64 * 1024 * 1024  # 64 MB
        if file_size <= MAX_CHUNK:
            chunk_size = file_size
            total_chunk_count = 1
        else:
            total_chunk_count = math.ceil(file_size / MAX_CHUNK)
            chunk_size = file_size // total_chunk_count

        if mime_type.startswith("image/"):
            # We use PULL_FROM_URL for images, using Cloudflare Tunnel URL from REDIRECT_URI
            from dotenv import load_dotenv
            import shutil
            
            load_dotenv()
            redirect_uri = os.getenv("REDIRECT_URI", "")
            base_url = redirect_uri.replace("/callback", "")
            if not base_url:
                raise Exception("REDIRECT_URI not configured. Cannot generate public URL for PULL_FROM_URL.")
                
            media_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
            os.makedirs(media_dir, exist_ok=True)
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(media_dir, file_name)
            shutil.copy(file_path, dest_path)
            
            public_url = f"{base_url}/media/{file_name}"
            logger.info(f"Using public URL for image: {public_url}")

            init_endpoint = "post/publish/content/init/"
            init_data = {
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO",
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "photo_cover_index": 1,
                    "photo_images": [public_url]
                },
                "post_info": {
                    "title": caption if caption else "Photo Upload",
                    "privacy_level": privacy_level,
                    "disable_comment": disable_comment,
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
                    "chunk_size": chunk_size,
                    "total_chunk_count": total_chunk_count
                },
                "post_info": {
                    "title": caption if caption else "Video Upload",
                    "privacy_level": privacy_level,
                    "disable_comment": disable_comment,
                    "disable_duet": disable_duet,
                    "disable_stitch": disable_stitch,
                }
            }
            
        try:
            logger.info(f"Initializing upload for {file_path}")
            init_response = api_client.post(init_endpoint, json=init_data)
            
            if "data" not in init_response:
                raise Exception(f"Failed to initialize upload: {init_response}")
                
            data = init_response["data"]
            upload_url = data.get("upload_url")
            publish_id = data.get("publish_id")
            
            if upload_url:
                logger.info(f"Uploading {total_chunk_count} chunk(s) to {upload_url}...")
                with open(file_path, "rb") as f:
                    for i in range(total_chunk_count):
                        start = i * chunk_size
                        # The final chunk takes all remaining bytes.
                        end = file_size - 1 if i == total_chunk_count - 1 else start + chunk_size - 1
                        length = end - start + 1
                        f.seek(start)
                        chunk_data = f.read(length)

                        upload_headers = {
                            "Content-Type": mime_type,
                            "Content-Length": str(length),
                            "Content-Range": f"bytes {start}-{end}/{file_size}",
                        }
                        upload_res = requests.put(upload_url, data=chunk_data, headers=upload_headers)
                        upload_res.raise_for_status()
                        logger.info(f"Uploaded chunk {i + 1}/{total_chunk_count} (bytes {start}-{end})")
                logger.info(f"Upload complete. Publish ID: {publish_id}")
            else:
                if not publish_id:
                    raise Exception(f"Init upload failed (missing upload_url and publish_id): {init_response}")
                logger.info(f"Publish ID received directly: {publish_id}")
                
            return publish_id
        except Exception as e:
            logger.error(f"Error during media upload: {e}")
            raise

    def publish(self, publish_id: str, caption: str = "", privacy_level: str = "SELF_ONLY"):
        """
        Commits the published video/image.
        For DIRECT_POST, this step is sometimes optional or handled automatically,
        but available here for INBOX workflows.
        """
        logger.info(f"Publishing post with ID: {publish_id}")
        endpoint = "post/publish/video/commit/"
        
        data = {
            "publish_id": publish_id,
            "post_info": {
                "title": caption,
                "privacy_level": privacy_level
            }
        }
        
        response = api_client.post(endpoint, json=data)
        logger.info(f"Publish response: {response}")
        
        if "error" in response and response["error"].get("code") != "ok":
            logger.error(f"Failed to publish post: {response}")
            raise Exception(f"Publish failed: {response['error'].get('message', 'Unknown error')}")
            
        return response

    def check_status(self, publish_id: str):
        logger.info(f"Checking status for post ID: {publish_id}")
        endpoint = "post/publish/status/fetch/"
        data = {"publish_id": publish_id}
        
        response = api_client.post(endpoint, json=data)
        if "data" in response and "status" in response["data"]:
            return response["data"]["status"]
        
        raise Exception(f"Failed to get status. Response: {response}")
