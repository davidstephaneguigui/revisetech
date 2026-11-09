from django.urls import path
from . import views

urlpatterns = [
    path('', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('sequence/<int:sequence_id>/publish/', views.publish_sequence, name='publish_sequence'),
    path('sequence/<int:sequence_id>/request_review/', views.request_second_review, name='request_second_review'),
]