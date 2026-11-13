from django.contrib import admin
from .models import Matiere, Chapter, Sequence, Session, Activity, Question, Choice

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'color_hex')
    filter_horizontal = ('classes',)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('name', 'matiere', 'status')
    list_filter = ('status', 'matiere')

@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'chapter', 'status')
    list_filter = ('status',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'sequence', 'status')
    list_filter = ('status',)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type', 'status')
    list_filter = ('activity_type', 'status')
    filter_horizontal = ('sessions',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'activity')
    list_filter = ('activity',)

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)