from django.db import models
from django.conf import settings

class Classe(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la classe")
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
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name

class Matiere(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la matière")
    color_hex = models.CharField(max_length=7, default="#333333", verbose_name="Couleur (hex)")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="subjects", 
        verbose_name="Enseignant"
    )
    classes = models.ManyToManyField(
        Classe, 
        related_name="subjects", 
        blank=True, 
        verbose_name="Classes associées"
    )
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"

    def __str__(self):
        return self.name

class Sequence(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la séquence")
    subjects = models.ManyToManyField(
        Matiere, 
        related_name="sequences", 
        blank=True, 
        verbose_name="Matières associées"
    )
    
    class Meta:
        verbose_name = "Séquence"
        verbose_name_plural = "Séquences"

    def __str__(self):
        return self.name

class Session(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la séance")
    sequences = models.ManyToManyField(
        Sequence, 
        related_name="sessions", 
        blank=True, 
        verbose_name="Séquences associées"
    )
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"

    def __str__(self):
        return self.name

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('COURSE', 'Cours'),
        ('TP', 'Travaux Pratiques'),
        ('EXERCISE', 'Exercice'),
        ('QUIZ', 'Quiz'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Titre de l'activité")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, verbose_name="Type d'activité")
    sessions = models.ManyToManyField(Session, related_name="activities", blank=True, verbose_name="Séances associées")
    
    # Content fields
    content = models.TextField(blank=True, null=True, verbose_name="Contenu textuel (Cours, consignes)")
    external_url = models.URLField(blank=True, null=True, verbose_name="Lien externe (Vidéo, simulateur...)")
    
    # File upload will handle SCORM (.zip), H5P (.h5p), PDF, Fritzing (.fzz), etc.
    file_upload = models.FileField(upload_to='activities/', blank=True, null=True, verbose_name="Fichier joint (SCORM, H5P, PDF...)")
    
    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"

    def __str__(self):
        return f"{self.title} ({self.get_activity_type_display()})"

class Question(models.Model):
    activity = models.ForeignKey(
        Activity, 
        on_delete=models.CASCADE, 
        related_name="questions", 
        limit_choices_to={'activity_type': 'QUIZ'},
        verbose_name="Activité (Quiz)"
    )
    text = models.TextField(verbose_name="Question")
    order = models.IntegerField(default=1, verbose_name="Ordre d'apparition")

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['order']

    def __str__(self):
        return f"{self.activity.title} - Q{self.order}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices", verbose_name="Question")
    text = models.CharField(max_length=255, verbose_name="Texte du choix")
    is_correct = models.BooleanField(default=False, verbose_name="Est la bonne réponse ?")

    class Meta:
        verbose_name = "Choix de réponse"
        verbose_name_plural = "Choix de réponses"

    def __str__(self):
        return self.text