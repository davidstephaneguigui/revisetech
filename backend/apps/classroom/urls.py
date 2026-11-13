from django.urls import path
from . import views

urlpatterns = [
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/classe/<int:class_id>/', views.class_detail, name='class_detail'),
    path('teacher/student/<int:student_id>/results/', views.student_results, name='student_results'),
    path('join/', views.join_class, name='join_class'),
    path('suggestions/', views.suggestion_list, name='suggestion_list'),
    path('teacher/results', views.teacher_results, name='teacher_results'),
    path('teacher/class/<int:class_id>/', views.class_results, name='class_results'),
    path('teacher/student/<int:student_id>/', views.student_profile, name='student_profile'),
    path('class/<int:class_id>/session/<int:session_id>/toggle/', views.toggle_session_completion, name='toggle_session_completion'),
    path('class/<int:class_id>/session/<int:session_id>/add-local/', views.create_local_activity, name='create_local_activity'),
    path('class/<int:class_id>/sequence/<int:sequence_id>/', views.class_sequence_detail, name='class_sequence_detail'),
    path('class/<int:class_id>/session/<int:session_id>/prepare/', views.prepare_session, name='prepare_session'),
    path('class/<int:class_id>/activity/<int:activity_id>/toggle-usage/', views.toggle_activity_usage, name='toggle_activity_usage'),
    path('class/<int:class_id>/session/<int:session_id>/activity/<int:activity_id>/move/<str:direction>/', views.move_activity, name='move_activity'),
    path('class/<int:class_id>/sequence/<int:sequence_id>/session/<int:session_id>/move/<str:direction>/', views.move_session, name='move_session'),
    path('activity/<int:activity_id>/import/', views.import_global_activity, name='import_global_activity'),
    path('class/<int:class_id>/session/<int:session_id>/add-existing/', views.add_existing_activity, name='add_existing_activity'),
    path('teacher/preparations/', views.teacher_preparations, name='teacher_preparations'),
]