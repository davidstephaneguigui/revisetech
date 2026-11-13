from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('help/', views.help_page, name='help_page'),
    path('stats/', views.apprenticeship_stats, name='apprenticeship_stats'),
]