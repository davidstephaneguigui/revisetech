from django.urls import path
from . import views

urlpatterns = [
    path('matiere/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('chapitre/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    path('sequence/<int:sequence_id>/', views.sequence_detail, name='sequence_detail'),
    path('seance/<int:session_id>/', views.session_detail, name='session_detail'),
    path('activite/<int:activity_id>/', views.activity_detail, name='activity_detail'),
    path('suggestion/<int:suggestion_id>/read/', views.mark_suggestion_read, name='mark_suggestion_read'),
]