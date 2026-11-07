from django import forms
from pedagogy.models import Sequence, Session, Activity, PlannedSession


class SequenceIntentionForm(forms.ModelForm):
    class Meta:
        model = Sequence
        fields = ['tags', 'objectives', 'modalities']
        widgets = {
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: binaire, logique, SIN, Arduino'}),
            'objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Objectifs pédagogiques de la séquence...'}),
            'modalities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Place dans la progression, prérequis...'}),
        }
        labels = {
            'tags': 'Mots-clés (Tags)',
            'objectives': 'Objectifs de la séquence',
            'modalities': 'Modalités et place dans la progression',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required
        self.fields['tags'].required = True
        self.fields['objectives'].required = True
        self.fields['modalities'].required = True


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


class PlannedSessionForm(forms.ModelForm):
    class Meta:
        model = PlannedSession
        fields = ['order', 'name', 'objective', 'session_type']
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Découverte du binaire'}),
            'objective': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Objectif principal...'}),
            'session_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'order': 'N°',
            'name': 'Titre',
            'objective': 'Objectif',
            'session_type': 'Type',
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