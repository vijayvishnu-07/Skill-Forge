from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:quiz_id>/', views.get_quiz_view, name='get_quiz'),
    path('<uuid:quiz_id>/submit/', views.submit_quiz_view, name='submit_quiz'),
]
