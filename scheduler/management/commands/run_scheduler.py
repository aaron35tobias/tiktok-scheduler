import time
from django.core.management.base import BaseCommand
from scheduler.service import start_scheduler, stop_scheduler

class Command(BaseCommand):
    help = 'Run the APScheduler background task processor'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting scheduler... Press Ctrl+C to stop.'))
        start_scheduler()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            stop_scheduler()
            self.stdout.write(self.style.WARNING('\nScheduler stopped.'))
