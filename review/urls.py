from django.urls import path
from . import views

urlpatterns = [
    path('', views.referee_dashboard, name='referee_dashboard'),
    path('sequence/<int:sequence_id>/submit/', views.submit_sequence, name='submit_sequence'),
    path('sequence/<int:sequence_id>/validate/', views.validate_sequence, name='validate_sequence'),
    path('sequence/<int:sequence_id>/reject/', views.reject_sequence, name='reject_sequence'),
    path('sequence/<int:sequence_id>/invalidate/', views.invalidate_sequence, name='invalidate_sequence'),
    path('sequence/<int:sequence_id_1>/compare/', views.compare_sequences, name='compare_sequences'),
]