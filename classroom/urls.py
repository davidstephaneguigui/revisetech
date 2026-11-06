from django.urls import path
from . import views

urlpatterns = [
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/classe/<int:class_id>/', views.class_detail, name='class_detail'),
    path('teacher/student/<int:student_id>/results/', views.student_results, name='student_results'),
    path('join/', views.join_class, name='join_class'),
]