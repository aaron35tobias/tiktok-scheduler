from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from scheduler.scheduler import schedule_post

class Command(BaseCommand):
    help = 'Schedule a new TikTok post'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to media file')
        parser.add_argument('--caption', type=str, required=True, help='Post caption')
        parser.add_argument('--delay', type=int, default=5, help='Minutes from now to schedule')

    def handle(self, *args, **options):
        file_path = options['file']
        caption = options['caption']
        delay = options['delay']

        scheduled_time = timezone.now() + datetime.timedelta(minutes=delay)
        
        try:
            post_id = schedule_post(file_path, caption, scheduled_time)
            self.stdout.write(self.style.SUCCESS(f'Successfully scheduled post ID: {post_id} for {scheduled_time} UTC'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to schedule: {e}'))
