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
]