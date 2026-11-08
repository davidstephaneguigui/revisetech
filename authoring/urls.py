from django.urls import path
from . import views

urlpatterns = [
    path('', views.designer_dashboard, name='designer_dashboard'),
    path('sequence/<int:sequence_id>/', views.manage_sequence, name='manage_sequence'),
    path('session/<int:session_id>/', views.manage_session, name='manage_session'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('activity/<int:activity_id>/questions/', views.manage_quiz_questions, name='manage_quiz_questions'),
    path('question/<int:question_id>/choices/', views.manage_question_choices, name='manage_question_choices'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
]