from django.urls import path
from . import views

urlpatterns = [
    path('generate/<uuid:enrollment_id>/', views.generate_certificate_view, name='generate_certificate'),
    path('<uuid:certificate_id>/download/', views.download_certificate_view, name='download_certificate'),
    path('verify/<str:certificate_id_str>/', views.verify_certificate_view, name='verify_certificate'),
]
