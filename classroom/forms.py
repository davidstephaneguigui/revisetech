from django import forms
from pedagogy.models import Matiere, Sequence, Activity
from .models import Classe, Suggestion


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['name', 'level', 'specialty']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Groupe A'}),
            'level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Première'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: STI2D'}),
        }
        labels = {
            'name': 'Nom de la classe',
            'level': 'Niveau',
            'specialty': 'Spécialité',
        }


class LocalActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'activity_type', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de l\'activité'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Contenu de l\'activité (texte, consignes...)'}),
        }


class AddStudentForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        label="Nom d'utilisateur de l'élève",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: jean.dupont'})
    )


class JoinClassForm(forms.Form):
    code_invitation = forms.CharField(
        max_length=20, 
        label="Code d'invitation",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: A1B2C3D4'})
    )


class AddSubjectToClassForm(forms.Form):
    matiere = forms.ModelChoiceField(
        queryset=Matiere.objects.none(), # We'll populate this in the view
        label="Choisir une matière",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class SuggestionForm(forms.ModelForm):
    class Meta:
        model = Suggestion
        fields = ['activity', 'message']
        widgets = {
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: Révise bien ce chapitre avant le prochain contrôle.'}),
        }
        labels = {
            'activity': 'Activité à suggérer',
            'message': 'Message (optionnel)',
        }


class AddSequenceToClassForm(forms.Form):
    sequences = forms.ModelMultipleChoiceField(
        queryset=Sequence.objects.none(), # We'll populate this in the view
        label="Choisir les séquences",
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'})
    )