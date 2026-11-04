from django.contrib import admin
from .models import Classe, Matiere, Sequence, Session, Activity, Question, Choice

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('name', 'main_teacher')
    # Allows selecting multiple students easily
    filter_horizontal = ('students',)

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'color_hex')
    filter_horizontal = ('classes',)

@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('subjects',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('sequences',)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'activity_type')
    list_filter = ('activity_type',)
    filter_horizontal = ('sessions',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'activity')
    list_filter = ('activity',)

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)