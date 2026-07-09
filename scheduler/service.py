import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from scheduler.jobs import process_pending_posts

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start_scheduler():
    logger.info("Starting scheduler service...")
    
    # Run the job every 1 minute to check for pending posts
    scheduler.add_job(
        process_pending_posts,
        trigger=IntervalTrigger(minutes=1),
        id='process_pending_posts',
        name='Process pending TikTok posts',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully.")

def stop_scheduler():
    logger.info("Stopping scheduler service...")
    scheduler.shutdown()
