from django.contrib import admin
from .models import Quiz, Question, Option, QuizAttempt


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4
    max_num = 4


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'pass_percentage', 'question_count')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'marks', 'order')
    inlines = [OptionInline]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total_marks', 'percentage', 'passed')
