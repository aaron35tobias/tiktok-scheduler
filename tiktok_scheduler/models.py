from django.db import models
from django.utils import timezone

class ScheduledPost(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Publishing', 'Publishing'),
        ('Published', 'Published'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    )
    file_path = models.CharField(max_length=500)
    caption = models.TextField(blank=True, null=True)
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Post {self.id} - {self.status} at {self.scheduled_time}"

class TikTokToken(models.Model):
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    expires_in = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "TikTok OAuth Tokens"
