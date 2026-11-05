from django.urls import path
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/classe/<int:class_id>/', views.class_detail, name='class_detail'),
    path('join/', views.join_class, name='join_class'),
    path('teacher/student/<int:student_id>/results/', views.student_results, name='student_results'),
    path('designer/', views.designer_dashboard, name='designer_dashboard'),
    path('designer/sequence/<int:sequence_id>/', views.manage_sequence, name='manage_sequence'),
    path('designer/session/<int:session_id>/', views.manage_session, name='manage_session'),
    path('designer/sequence/<int:sequence_id>/submit/', views.submit_sequence, name='submit_sequence'),
    path('referee/', views.referee_dashboard, name='referee_dashboard'),
]