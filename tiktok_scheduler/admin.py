from django.contrib import admin
from .models import ScheduledPost, TikTokToken

@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_path', 'scheduled_time', 'status', 'retry_count')
    list_filter = ('status',)

@admin.register(TikTokToken)
class TikTokTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')
