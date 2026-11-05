from django.db import models
from django.conf import settings
from pedagogy.models import Activity

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