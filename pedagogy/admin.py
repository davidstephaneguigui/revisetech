from django.contrib import admin
from .models import (
    Classe, Matiere, Chapter, Sequence, Session, 
    Activity, Question, Choice, Result, Suggestion
)

# --- Inlines ---
# Allows adding choices directly inside the Question page
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4 # Shows 4 empty choice fields by default

# Allows adding questions directly inside the Activity page
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

# --- Admin Classes ---
@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'specialty', 'main_teacher')
    filter_horizontal = ('students',)

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'color_hex')
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
    inlines = [QuestionInline] # <--- Adds questions here

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'activity')
    list_filter = ('activity',)
    inlines = [ChoiceInline] # <--- Adds choices here

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity', 'score', 'max_score', 'date_attempt')
    list_filter = ('activity',)

@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('student', 'activity', 'teacher', 'is_read', 'created_at')
    list_filter = ('is_read',)