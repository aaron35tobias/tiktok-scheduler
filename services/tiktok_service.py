import logging
from datetime import datetime
from tiktok_scheduler.models import ScheduledPost

logger = logging.getLogger(__name__)

def schedule_post(file_path: str, caption: str, scheduled_time: datetime):
    """
    Schedules a new post.
    """
    try:
        new_post = ScheduledPost.objects.create(
            file_path=file_path,
            caption=caption,
            scheduled_time=scheduled_time,
            status="Pending"
        )
        logger.info(f"Successfully scheduled post ID: {new_post.id} for {scheduled_time}")
        return new_post.id
    except Exception as e:
        logger.error(f"Failed to schedule post: {e}")
        raise

def cancel_post(post_id: int):
    """
    Cancels a pending post.
    """
    try:
        post = ScheduledPost.objects.get(id=post_id)
        if post.status != "Pending":
            raise ValueError(f"Cannot cancel post with status '{post.status}'.")
            
        post.status = "Cancelled"
        post.save()
        logger.info(f"Successfully cancelled post ID: {post_id}")
        return True
    except ScheduledPost.DoesNotExist:
        logger.error(f"Post with ID {post_id} not found.")
        raise ValueError(f"Post with ID {post_id} not found.")
    except Exception as e:
        logger.error(f"Failed to cancel post ID: {post_id} - {e}")
        raise

def get_post_status_from_db(post_id: int):
    """
    Gets the current status of a scheduled post from the local DB.
    """
    try:
        post = ScheduledPost.objects.get(id=post_id)
        return post.status
    except ScheduledPost.DoesNotExist:
        raise ValueError(f"Post with ID {post_id} not found.")
