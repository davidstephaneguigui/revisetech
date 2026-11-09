from django import forms
from .models import ReviewAction

class DevalidationForm(forms.ModelForm):
    class Meta:
        model = ReviewAction
        fields = ['reason', 'comment']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Expliquez pourquoi vous rejetez ou annulez cette validation...'}),
        }
        labels = {
            'reason': 'Motif',
            'comment': 'Commentaire explicatif (obligatoire)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the comment field mandatory
        self.fields['comment'].required = True