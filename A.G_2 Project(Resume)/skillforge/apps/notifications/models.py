import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """In-app notification for users."""

    class NotificationType(models.TextChoices):
        COURSE_UPDATE = 'course_update', 'Course Update'
        ENROLLMENT = 'enrollment', 'New Enrollment'
        FEEDBACK = 'feedback', 'New Feedback'
        QUIZ_RESULT = 'quiz_result', 'Quiz Result'
        CERTIFICATE = 'certificate', 'Certificate Issued'
        SYSTEM = 'system', 'System'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}: {self.title}"
