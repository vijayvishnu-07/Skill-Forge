from django.contrib import admin
from .models import Category, Course, Module, Lesson, Enrollment, Progress, Bookmark, History


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_featured', 'course_count')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_featured',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'status', 'student_count', 'average_rating', 'is_featured')
    list_filter = ('status', 'skill_level', 'is_featured', 'category')
    search_fields = ('title', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'status')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'lesson_type', 'order')
    list_filter = ('lesson_type',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'completed')
    list_filter = ('completed',)


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'completed', 'watch_duration')


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'created_at')


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'last_accessed')
