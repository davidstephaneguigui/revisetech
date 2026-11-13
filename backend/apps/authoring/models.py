from django.db import models


class ActivityProposal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('REJECTED', 'Refusée'),
    ]
    
    activity = models.ForeignKey(
        'pedagogy.Activity', 
        on_delete=models.CASCADE, 
        related_name='authoring_proposals' # <-- Le nom unique
    )
    teacher = models.ForeignKey(
        'accounts.User', 
        on_delete=models.CASCADE,
        related_name='authoring_proposals' # <-- Le nom unique
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proposition : {self.activity.title} par {self.teacher.username}"