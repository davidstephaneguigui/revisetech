from django.urls import path

from .views import publishing as views

urlpatterns = [
    path('', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('sequence/<int:sequence_id>/publish/', views.publish_sequence, name='publish_sequence'),
    path('sequence/<int:sequence_id>/request_review/', views.request_second_review, name='request_second_review'),
    path('sequence/<int:sequence_id>/unpublish/', views.unpublish_sequence, name='unpublish_sequence'),
    path('sequence/<int:sequence_id>/stats/', views.sequence_stats, name='sequence_stats'),
    path('sequence/<int:sequence_id>/exam/', views.supervisor_sequence_exam, name='supervisor_sequence_exam'),
]