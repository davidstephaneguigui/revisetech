from django.urls import include, path

urlpatterns = [
    path('review/', include('apps.regulation.review_urls')),
    path('publishing/', include('apps.regulation.publishing_urls')),
]