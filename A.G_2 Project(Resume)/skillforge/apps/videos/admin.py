from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'duration', 'file_size', 'uploaded_at')
