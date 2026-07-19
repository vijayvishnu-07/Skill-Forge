import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Category(models.Model):
    """Course category for organization and filtering."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    icon = models.CharField(max_length=50, blank=True, default='📚')
    description = models.TextField(blank=True, default='')
    is_featured = models.BooleanField(default=False)
    course_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Core course model with full metadata and AI-generated fields."""

    class SkillLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        ALL_LEVELS = 'all_levels', 'All Levels'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        PRIVATE = 'private', 'Private'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_courses'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    caption = models.CharField(max_length=300, blank=True, default='')
    description = models.TextField(blank=True, default='')
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    skill_level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices,
        default=SkillLevel.ALL_LEVELS
    )
    language = models.CharField(max_length=50, default='English')
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # AI-generated fields
    learning_outcomes = models.JSONField(default=list, blank=True)
    prerequisites = models.JSONField(default=list, blank=True)
    highlights = models.JSONField(default=list, blank=True)
    ai_summary = models.TextField(blank=True, default='')

    # Computed stats
    total_duration = models.PositiveIntegerField(default=0, help_text='Duration in seconds')
    total_videos = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    student_count = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)

    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['-average_rating']),
            models.Index(fields=['-student_count']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def duration_display(self):
        """Return human-readable duration."""
        hours = self.total_duration // 3600
        minutes = (self.total_duration % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def update_stats(self):
        """Recalculate course statistics from modules/lessons."""
        from apps.videos.models import Video
        modules = self.modules.all()
        total_lessons = 0
        total_videos = 0
        total_duration = 0
        for module in modules:
            lessons = module.lessons.all()
            total_lessons += lessons.count()
            for lesson in lessons:
                if hasattr(lesson, 'video'):
                    total_videos += 1
                    total_duration += lesson.video.duration or 0
        self.total_lessons = total_lessons
        self.total_videos = total_videos
        self.total_duration = total_duration
        self.save(update_fields=['total_lessons', 'total_videos', 'total_duration'])


class Module(models.Model):
    """Course module/section grouping lessons."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    order = models.PositiveIntegerField(default=0)
    duration = models.PositiveIntegerField(default=0, help_text='Duration in seconds')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'modules'
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def update_duration(self):
        total = 0
        for lesson in self.lessons.all():
            if hasattr(lesson, 'video') and lesson.video.duration:
                total += lesson.video.duration
        self.duration = total
        self.save(update_fields=['duration'])


class Lesson(models.Model):
    """Individual lesson within a module (video or quiz type)."""

    class LessonType(models.TextChoices):
        VIDEO = 'video', 'Video'
        QUIZ = 'quiz', 'Quiz'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=10, choices=LessonType.choices, default=LessonType.VIDEO)
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lessons'
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Enrollment(models.Model):
    """Student enrollment in a course with completion tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'enrollments'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.email} → {self.course.title}"

    @property
    def progress_percentage(self):
        total = self.course.total_lessons
        if total == 0:
            return 0
        completed = self.progress_records.filter(completed=True).count()
        return int((completed / total) * 100)


class Progress(models.Model):
    """Per-lesson progress tracking for resume functionality."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    completed = models.BooleanField(default=False)
    watch_duration = models.PositiveIntegerField(default=0, help_text='Seconds watched')
    last_position = models.PositiveIntegerField(default=0, help_text='Last playback position in seconds')
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'progress'
        unique_together = ['enrollment', 'lesson']

    def __str__(self):
        return f"Progress: {self.enrollment.student.email} - {self.lesson.title}"


class Bookmark(models.Model):
    """User bookmark for a lesson with optional note."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='bookmarks')
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookmarks'
        unique_together = ['user', 'lesson']
        ordering = ['-created_at']

    def __str__(self):
        return f"Bookmark: {self.user.email} - {self.lesson.title}"


class History(models.Model):
    """Track user's course viewing history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_history'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='view_history')
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'history'
        unique_together = ['user', 'course']
        ordering = ['-last_accessed']

    def __str__(self):
        return f"History: {self.user.email} - {self.course.title}"
