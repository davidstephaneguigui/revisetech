from django import forms
from pedagogy.models import Classe, Matiere

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