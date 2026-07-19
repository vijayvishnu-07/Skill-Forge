import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with email as primary identifier and role support."""

    class Role(models.TextChoices):
        STUDENT = 'student', _('Student')
        INSTRUCTOR = 'instructor', _('Instructor')
        ADMIN = 'admin', _('Admin')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class Profile(models.Model):
    """Extended user profile with bio, skills, and social links."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    headline = models.CharField(max_length=200, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    website = models.URLField(blank=True, default='')
    skills = models.JSONField(default=list, blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'

    def __str__(self):
        return f"Profile of {self.user.email}"

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.svg'
