from django.conf import settings
from django.db import models

from apps.pedagogy.models import Activity, Sequence


class Result(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results", verbose_name="Élève")
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="results", verbose_name="Activité")
    score = models.IntegerField(verbose_name="Score obtenu")
    max_score = models.IntegerField(verbose_name="Score maximum")
    date_attempt = models.DateTimeField(auto_now_add=True, verbose_name="Date de la tentative")

    class Meta:
        verbose_name = "Résultat"
        verbose_name_plural = "Résultats"

    def __str__(self):
        return f"{self.student.username} - {self.activity.title} : {self.score}/{self.max_score}"


class Badge(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges", verbose_name="Élève")
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name="badges", verbose_name="Séquence")
    date_obtained = models.DateTimeField(auto_now_add=True, verbose_name="Date d'obtention")

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        # Ensure a student can only have one badge per sequence
        unique_together = ('student', 'sequence')

    def __str__(self):
        return f"{self.student.username} - {self.sequence.name}"