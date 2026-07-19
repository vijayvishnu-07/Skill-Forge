from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_view, name='notifications'),
    path('<uuid:notification_id>/read/', views.mark_read_view, name='mark_notification_read'),
    path('read-all/', views.mark_all_read_view, name='mark_all_read'),
]
