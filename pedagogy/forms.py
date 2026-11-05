from django import forms
from .models import Sequence, Chapter, Session


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