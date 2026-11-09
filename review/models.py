from django.db import models
from django.conf import settings
from pedagogy.models import Sequence

class ReviewAction(models.Model):
    """
    Logs every devalidation or rejection action made by a referee.
    """
    ACTION_TYPES = [
        ('REJECT_INTENT', "Rejet de l'intention"),
        ('INVALIDATE_INTENT', "Annulation de la validation de l'intention"),
        ('REJECT_CONTENT', "Rejet du contenu"),
        ('INVALIDATE_CONTENT', "Annulation de la validation du contenu"),
    ]
    
    REASONS = [
        ('NOT_RELEVANT', 'Non pertinente'),
        ('ALREADY_DONE', 'Déjà réalisée par un autre enseignant'),
        ('ERROR', 'Erreur dans le contenu'),
        ('OTHER', 'Autre'),
    ]

    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name="review_actions", verbose_name="Séquence")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Référent")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Type d'action")
    reason = models.CharField(max_length=20, choices=REASONS, verbose_name="Motif")
    comment = models.TextField(verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        verbose_name = "Action de révision"
        verbose_name_plural = "Actions de révision"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.sequence.name} par {self.user.username if self.user else 'Inconnu'}"