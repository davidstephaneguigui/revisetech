import uuid
from django.db import models
from django.conf import settings
from pedagogy.models import Activity, Session


class Classe(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la classe")
    level = models.CharField(max_length=50, verbose_name="Niveau (ex: Première)")
    specialty = models.CharField(max_length=50, verbose_name="Spécialité (ex: STI2D)")
    code_invitation = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Code d'invitation")
    main_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="main_classes", 
        verbose_name="Professeur principal"
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name="student_classes", 
        blank=True, 
        verbose_name="Élèves"
    )
    sequences = models.ManyToManyField(
        'pedagogy.Sequence', 
        related_name="classes", 
        blank=True, 
        verbose_name="Séquences au programme"
    )
    
    def save(self, *args, **kwargs):
        if not self.code_invitation:
            # Generate a short, unique code (8 characters)
            self.code_invitation = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"

    def __str__(self):
        return f"{self.name} ({self.level} {self.specialty})"


class SessionCompletion(models.Model):
    classe = models.ForeignKey('Classe', on_delete=models.CASCADE, related_name='completed_sessions')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='completions')
    is_completed = models.BooleanField(default=False, verbose_name="Séance réalisée")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('classe', 'session')
        verbose_name = "Suivi de réalisation"
        verbose_name_plural = "Suivis de réalisation"

    def __str__(self):
        return f"{self.classe.name} - {self.session.name} : {'Fait' if self.is_completed else 'Non fait'}"


class ActivitySelection(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='selected_activities')
    activity = models.ForeignKey('pedagogy.Activity', on_delete=models.CASCADE, related_name='selections')
    is_used = models.BooleanField(default=True, verbose_name="Activité utilisée")

    class Meta:
        unique_together = ('classe', 'activity')
        verbose_name = "Sélection d'activité"
        verbose_name_plural = "Sélections d'activités"

    def __str__(self):
        return f"{self.classe.name} - {self.activity.title} : {'Oui' if self.is_used else 'Non'}"


class Suggestion(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_suggestions", verbose_name="Enseignant")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_suggestions", verbose_name="Élève")
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, verbose_name="Activité suggérée")
    message = models.TextField(blank=True, null=True, verbose_name="Message personnalisé")
    is_read = models.BooleanField(default=False, verbose_name="Lu par l'élève")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Suggestion"
        verbose_name_plural = "Suggestions"

    def __str__(self):
        return f"Suggestion pour {self.student.username} - {self.activity.title}"
