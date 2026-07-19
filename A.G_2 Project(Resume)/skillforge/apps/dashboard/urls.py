from django.urls import path
from apps.courses.views import landing_view
from . import views

urlpatterns = [
    path('', landing_view, name='landing'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard_view, name='instructor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/admin/users/', views.admin_users_view, name='admin_users'),
    path('dashboard/admin/courses/', views.admin_courses_view, name='admin_courses'),
    path('dashboard/admin/categories/', views.admin_categories_view, name='admin_categories'),
    path('dashboard/admin/feedback/', views.admin_feedback_view, name='admin_feedback'),
    path('dashboard/admin/settings/', views.admin_settings_view, name='admin_settings'),
]
