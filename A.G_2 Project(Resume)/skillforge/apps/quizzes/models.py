import uuid
from django.db import models


class Quiz(models.Model):
    """Quiz attached to a lesson with pass criteria."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.OneToOneField(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='quiz'
    )
    pass_percentage = models.PositiveIntegerField(default=70)
    time_limit = models.PositiveIntegerField(default=0, help_text='Time limit in minutes, 0 = no limit')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quizzes'
        verbose_name_plural = 'quizzes'

    def __str__(self):
        return f"Quiz: {self.lesson.title}"

    @property
    def total_marks(self):
        return self.questions.aggregate(total=models.Sum('marks'))['total'] or 0

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    """Multiple choice question within a quiz."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    explanation = models.TextField(blank=True, default='')
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questions'
        ordering = ['order']

    def __str__(self):
        return f"Q: {self.text[:50]}"


class Option(models.Model):
    """Answer option for a question (A, B, C, D)."""

    LABEL_CHOICES = [
        ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=1, choices=LABEL_CHOICES)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = 'options'
        ordering = ['label']

    def __str__(self):
        return f"{self.label}: {self.text[:30]}"


class QuizAttempt(models.Model):
    """Record of a student's quiz attempt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total_marks = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-attempted_at']

    def __str__(self):
        return f"{self.student.email} - {self.quiz.lesson.title}: {self.percentage}%"
