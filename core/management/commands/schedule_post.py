import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from tiktok_scheduler.models import Post
from tiktok_scheduler.storage import Storage
from core.tasks import upload_post_task

class Command(BaseCommand):
    help = 'Schedules a video or image to be posted on TikTok'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to the video (.mp4) or image file')
        parser.add_argument('--caption', type=str, default='', help='Caption for the post')
        parser.add_argument('--delay', type=int, default=0, help='Delay in minutes before posting')

    def handle(self, *args, **options):
        file_path = options['file']
        caption = options['caption']
        delay = options['delay']

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        token = Storage.load_tokens()
        if not token or not token.access_token:
            self.stderr.write(self.style.ERROR("No TikTok access token found."))
            self.stderr.write(self.style.WARNING("Please run 'python start_all.py' and authenticate via the browser first."))
            return

        run_date = datetime.now() + timedelta(minutes=delay)
        schedule_time_str = run_date.isoformat()

        post = Post(
            id=None,
            media=os.path.abspath(file_path),
            caption=caption,
            schedule=schedule_time_str
        )

        posts = Storage.load_schedule()
        posts.append(post)
        Storage.save_schedule(posts)

        # Schedule the Celery task (using ETA)
        self.stdout.write(self.style.SUCCESS(f"Scheduling post for {schedule_time_str}..."))
        upload_post_task.apply_async((post.id,), eta=run_date)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully queued post {post.id}. Make sure the Celery worker is running!"))
