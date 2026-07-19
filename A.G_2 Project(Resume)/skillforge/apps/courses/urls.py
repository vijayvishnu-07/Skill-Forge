from django.urls import path
from . import views

urlpatterns = [
    path('', views.browse_courses_view, name='browse_courses'),
    path('search/', views.search_courses_view, name='search_courses'),
    path('create/step-1/', views.course_create_step1_view, name='course_create_step1'),
    path('create/step-2/', views.course_create_step2_view, name='course_create_step2'),
    path('create/step-3/', views.course_create_step3_view, name='course_create_step3'),
    path('create/review/', views.course_review_view, name='course_review'),
    path('progress/update/', views.update_progress_view, name='update_progress'),
    path('bookmark/toggle/', views.toggle_bookmark_view, name='toggle_bookmark'),
    path('module/add/', views.add_module_view, name='add_module'),
    path('module/<uuid:module_id>/', views.update_module_view, name='update_module'),
    path('lesson/add/', views.add_lesson_view, name='add_lesson'),
    path('lesson/<uuid:lesson_id>/delete/', views.delete_lesson_view, name='delete_lesson'),
    path('quiz/question/add/', views.add_quiz_question_view, name='add_quiz_question'),
    path('<slug:slug>/', views.course_detail_view, name='course_detail'),
    path('<slug:slug>/enroll/', views.enroll_course_view, name='course_enroll'),
    path('<slug:slug>/watch/', views.course_watch_view, name='course_watch'),
    path('<slug:slug>/edit/', views.course_edit_view, name='course_edit'),
    path('<slug:slug>/delete/', views.course_delete_view, name='course_delete'),
]
