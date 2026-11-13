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
    path('activity/<int:activity_id>/edit/', views.edit_activity, name='edit_activity'),
    path('session/<int:session_id>/edit/', views.edit_session, name='edit_session'),
    path('session/<int:session_id>/move/<str:direction>/', views.move_session, name='move_session'),
    path('sequence/<int:sequence_id>/delete/', views.delete_sequence, name='delete_sequence'),
    path('sequence/create', views.create_sequence, name='create_sequence'),
    path('activity/<int:activity_id>/propose/', views.propose_activity, name='propose_activity'),
    path('proposals/', views.designer_proposals, name='designer_proposals'),
    path('proposals/<int:proposal_id>/<str:action>/', views.handle_proposal, name='handle_proposal'),
    path('activity-bank/', views.activity_bank, name='activity_bank'),
    path('chapter/<int:chapter_id>/', views.designer_chapter_detail, name='designer_chapter_detail'),
]