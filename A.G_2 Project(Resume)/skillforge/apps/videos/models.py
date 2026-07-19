import uuid
from django.db import models


class Video(models.Model):
    """Video file attached to a lesson with duration tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.OneToOneField(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='video'
    )
    file = models.FileField(upload_to='videos/')
    duration = models.PositiveIntegerField(default=0, help_text='Duration in seconds')
    file_size = models.PositiveBigIntegerField(default=0, help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'videos'

    def __str__(self):
        return f"Video: {self.lesson.title}"

    @property
    def duration_display(self):
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes}:{seconds:02d}"
