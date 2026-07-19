from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:course_id>/submit/', views.submit_feedback_view, name='submit_feedback'),
    path('<uuid:course_id>/', views.get_feedback_view, name='get_feedback'),
]
