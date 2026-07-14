import logging
from celery import shared_task
from tiktok_scheduler.uploader import TikTokUploader
from tiktok_scheduler.storage import Storage
from tiktok_scheduler.models import Post

logger = logging.getLogger(__name__)

@shared_task
def upload_post_task(post_id):
    logger.info(f"Celery executing upload_post_task for {post_id}")
    uploader = TikTokUploader()
    
    posts = Storage.load_schedule()
    post = next((p for p in posts if p.id == post_id), None)
    
    if not post:
        logger.error(f"Post {post_id} not found in schedule.")
        return

    try:
        post.status = "Uploading"
        Storage.save_schedule(posts)

        publish_id = uploader.upload_media(
            post.media,
            post.full_caption,
            privacy_level=post.privacy or "SELF_ONLY",
            disable_comment=not post.allow_comments,
            disable_duet=not post.allow_duet,
            disable_stitch=not post.allow_stitch,
        )
        
        post.publish_id = publish_id
        post.status = "Published"
        post.error_message = None
        logger.info(f"Successfully published post {post_id}")
        
    except Exception as e:
        post.status = "Failed"
        post.error_message = str(e)
        logger.error(f"Failed to publish post {post_id}: {e}")
        
    finally:
        Storage.save_schedule(posts)
