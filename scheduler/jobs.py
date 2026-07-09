import logging
from django.utils import timezone
from scheduler.models import ScheduledPost
from tiktok.services.upload import upload_media
from tiktok.services.publisher import publish_post
from tiktok.services.authentication import refresh_access_token

logger = logging.getLogger(__name__)

def process_pending_posts():
    """
    Checks the database for pending posts whose scheduled time has arrived or passed,
    and attempts to publish them.
    """
    logger.info("Checking for pending posts...")
    try:
        now = timezone.now()
        pending_posts = ScheduledPost.objects.filter(
            status="Pending",
            scheduled_time__lte=now
        )
        
        if not pending_posts.exists():
            logger.info("No pending posts to process at this time.")
            return
            
        # Refresh token proactively if we have posts to process
        try:
            refresh_access_token()
        except Exception as e:
            logger.error(f"Failed to refresh token before processing posts: {e}")
            
        for post in pending_posts:
            logger.info(f"Processing post ID: {post.id}")
            post.status = "Publishing"
            post.save()
            
            try:
                # 1. Upload media
                publish_id = upload_media(post.file_path)
                
                # 2. Publish post
                publish_post(publish_id, caption=post.caption)
                
                # Success
                post.status = "Published"
                logger.info(f"Successfully published post ID: {post.id}")
                
            except Exception as e:
                logger.error(f"Failed to publish post ID: {post.id} - {e}")
                post.retry_count += 1
                if post.retry_count >= 3:
                    post.status = "Failed"
                    logger.error(f"Post ID: {post.id} failed after max retries.")
                else:
                    post.status = "Pending"  # Revert to pending for next cycle
                    logger.info(f"Post ID: {post.id} will be retried. Retry count: {post.retry_count}")
            
            post.save()
            
    except Exception as e:
        logger.error(f"Error in process_pending_posts: {e}")
