from django.urls import path
from . import views

urlpatterns = [
    path('', views.referee_dashboard, name='referee_dashboard'),
    path('sequence/<int:sequence_id>/validate/', views.validate_sequence, name='validate_sequence'),
    path('sequence/<int:sequence_id>/reject/', views.reject_sequence, name='reject_sequence'),
    path('sequence/<int:sequence_id>/invalidate/', views.invalidate_sequence, name='invalidate_sequence'),
    path('sequence/<int:sequence_id_1>/compare/', views.compare_sequences, name='compare_sequences'),
    path('sequence/<int:sequence_id>/submit-content/', views.submit_content, name='submit_content'),
    path('sequence/<int:sequence_id>/validate-content/', views.validate_content, name='validate_content'),
    path('inspector/', views.inspector_dashboard, name='inspector_dashboard'),
    path('sequence/<int:sequence_id>/publish/', views.publish_sequence, name='publish_sequence'),
    path('sequence/<int:sequence_id>/request_second_review/', views.request_second_review, name='request_second_review'),
]