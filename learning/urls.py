from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_home, name='student_home'),
    path('progression/', views.student_progression, name='student_progression'),
]