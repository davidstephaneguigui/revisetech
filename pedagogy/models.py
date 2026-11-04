from django.db import models
from django.conf import settings
import uuid


# Common choices for validation workflow
STATUS_CHOICES = [
    ('DRAFT', 'Brouillon'),
    ('PENDING', 'En attente de validation'),
    ('VALIDATED', 'Validé'),
    ('PUBLISHED', 'Publié'),
    ('REJECTED', 'Rejeté'),
]


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


class Chapter(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom du chapitre/module")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    matiere = models.ForeignKey(
        Matiere, 
        on_delete=models.CASCADE, 
        related_name="chapters", 
        verbose_name="Matière"
    )
    
    class Meta:
        verbose_name = "Chapitre / Module"
        verbose_name_plural = "Chapitres / Modules"

    def __str__(self):
        return f"{self.matiere.name} - {self.name}"


class Sequence(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la séquence")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    chapter = models.ForeignKey(
        Chapter, 
        on_delete=models.CASCADE, 
        related_name="sequences", 
        verbose_name="Chapitre"
    )
    
    class Meta:
        verbose_name = "Séquence"
        verbose_name_plural = "Séquences"

    def __str__(self):
        return self.name


class Session(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la séance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    sequence = models.ForeignKey(
        Sequence, 
        on_delete=models.CASCADE, 
        related_name="sessions", 
        verbose_name="Séquence"
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    sessions = models.ManyToManyField(Session, related_name="activities", blank=True, verbose_name="Séances associées")
    
    content = models.TextField(blank=True, null=True, verbose_name="Contenu textuel (Cours, consignes)")
    external_url = models.URLField(blank=True, null=True, verbose_name="Lien externe (Vidéo, simulateur...)")
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