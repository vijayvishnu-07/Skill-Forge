"""
URL configuration for Skill Forge.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('courses/', include('apps.courses.urls')),
    path('quizzes/', include('apps.quizzes.urls')),
    path('feedback/', include('apps.feedback.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('certificates/', include('apps.certificates.urls')),
    path('api/v1/', include('apps.api.urls')),
    path('auth/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
