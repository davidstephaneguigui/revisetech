from django.urls import path
from . import views

urlpatterns = [
    path('', views.designer_dashboard, name='designer_dashboard'),
    path('sequence/<int:sequence_id>/', views.manage_sequence, name='manage_sequence'),
    path('session/<int:session_id>/', views.manage_session, name='manage_session'),
]