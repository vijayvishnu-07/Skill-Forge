import uuid
from django.db import models


class Certificate(models.Model):
    """Completion certificate for a course enrollment."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(
        'courses.Enrollment',
        on_delete=models.CASCADE,
        related_name='certificate'
    )
    certificate_id = models.CharField(max_length=20, unique=True)
    file = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'certificates'

    def __str__(self):
        return f"Certificate {self.certificate_id}"

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            import random
            import string
            self.certificate_id = 'SF-' + ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=12)
            )
        super().save(*args, **kwargs)
