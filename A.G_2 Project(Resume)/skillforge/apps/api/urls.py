"""REST API URL router for Skill Forge v1."""
from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path('courses/', include('apps.courses.urls')),
    path('quizzes/', include('apps.quizzes.urls')),
    path('feedback/', include('apps.feedback.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('certificates/', include('apps.certificates.urls')),
]
