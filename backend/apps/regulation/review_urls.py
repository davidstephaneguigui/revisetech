from django.urls import path

from .views import review as views

urlpatterns = [
    path('', views.referee_dashboard, name='referee_dashboard'),
    path('sequence/<int:sequence_id>/validate/', views.validate_sequence, name='validate_sequence'),
    path('sequence/<int:sequence_id>/reject/', views.reject_sequence, name='reject_sequence'),
    path('sequence/<int:sequence_id>/invalidate/', views.invalidate_sequence, name='invalidate_sequence'),
    path('sequence/<int:sequence_id_1>/compare/', views.compare_sequences, name='compare_sequences'),
    path('sequence/<int:sequence_id>/submit-content/', views.submit_content, name='submit_content'),
    path('sequence/<int:sequence_id>/validate-content/', views.validate_content, name='validate_content'),
    path('chapter/<int:chapter_id>/', views.referee_chapter_detail, name='referee_chapter_detail'),
    path('sequence/<int:sequence_id>/exam/', views.referee_sequence_exam, name='referee_sequence_exam'),
]