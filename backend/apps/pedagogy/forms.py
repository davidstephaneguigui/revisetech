from django import forms

from .models import Activity, Chapter, Sequence, Session


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ['name', 'matiere']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: SIN'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Nom du chapitre / module',
            'matiere': 'Matière associée',
        }


class SequenceForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ['name', 'chapter']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Numération'}),
            'chapter': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Nom de la séquence',
            'chapter': 'Chapitre parent',
        }


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Binaire vs décimal'}),
        }
        labels = {
            'name': 'Nom de la séance',
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'activity_type', 'content', 'external_url', 'file_upload']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Exercice de conversion'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Contenu du cours ou consignes...'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'file_upload': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Titre de l\'activité',
            'activity_type': 'Type d\'activité',
            'content': 'Contenu textuel',
            'external_url': 'Lien externe (optionnel)',
            'file_upload': 'Fichier joint (optionnel)',
        }