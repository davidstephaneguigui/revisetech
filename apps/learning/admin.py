from django.contrib import admin
from .models import Result, Badge

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity', 'score', 'max_score', 'date_attempt')
    list_filter = ('activity', 'student')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'sequence', 'date_obtained')
    list_filter = ('sequence', 'student')