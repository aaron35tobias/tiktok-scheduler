import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger

from .storage import Storage
from .uploader import TikTokUploader
from .models import Post

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.uploader = TikTokUploader()

    def _process_post(self, post_id: str):
        # Reload the schedule to get the latest post state
        posts = Storage.load_schedule()
        post = next((p for p in posts if p.id == post_id), None)
        
        if not post:
            logger.error(f"Post {post_id} not found in schedule.")
            return

        if post.status != "Pending" and post.status != "Retry":
            logger.info(f"Skipping post {post_id} because status is {post.status}")
            return

        try:
            # Update status to Uploading
            post.status = "Uploading"
            Storage.save_schedule(posts)
            
            logger.info(f"Starting upload for post {post_id}: {post.media}")
            publish_id = self.uploader.upload_media(post.media, post.caption)
            
            # (Optional) if you want to call commit here
            # self.uploader.publish(publish_id, post.caption)
            
            post.publish_id = publish_id
            post.status = "Published"
            post.error_message = None
            logger.info(f"Successfully published post {post_id} with publish_id {publish_id}")
            
        except Exception as e:
            post.status = "Failed"
            post.error_message = str(e)
            logger.error(f"Failed to publish post {post_id}: {e}")
            
        finally:
            # Always save final state
            Storage.save_schedule(posts)

    def load_jobs(self):
        posts = Storage.load_schedule()
        now = datetime.now()
        
        for post in posts:
            if post.status in ["Pending", "Retry"]:
                try:
                    # Format e.g., "2026-07-11 09:00:00" or "2026-07-11 09:00"
                    run_date = datetime.fromisoformat(post.schedule)
                    
                    if run_date <= now:
                        logger.warning(f"Post {post.id} is scheduled in the past. It will execute immediately.")
                    
                    self.scheduler.add_job(
                        self._process_post,
                        trigger=DateTrigger(run_date=run_date),
                        args=[post.id],
                        id=post.id,
                        replace_existing=True
                    )
                    logger.info(f"Queued post {post.id} for {run_date}")
                except ValueError as e:
                    logger.error(f"Invalid schedule format for post {post.id}: {post.schedule}. Error: {e}")

    def start(self):
        logger.info("Loading jobs from schedule.json...")
        self.load_jobs()
        logger.info("Starting APScheduler (Press Ctrl+C to stop)...")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
