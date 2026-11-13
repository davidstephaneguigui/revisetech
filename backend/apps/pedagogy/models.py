from django.conf import settings
from django.db import models

STATUS_CHOICES = [
    ('DRAFT', 'Brouillon'),
    ('PENDING', 'Intention en attente'),
    ('VALIDATED', 'Intention validée'),
    ('CONTENT_PENDING', 'Contenu à valider'),
    ('CONTENT_VALIDATED', 'Contenu validé'),
    ('PENDING_PUBLISHING', "Contenu à publier"),
    ('PUBLISHED', 'Publié'),
    ('UNPUBLISHED', 'Dépublié'),
    ('ARCHIVED', 'Archivé'),
    ('REJECTED', 'Rejeté'),
]


class Matiere(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la matière")
    color_hex = models.CharField(max_length=7, default="#333333", verbose_name="Couleur (hex)")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="created_subjects", 
        verbose_name="Concepteur"
    )
    classes = models.ManyToManyField(
        'classroom.Classe', 
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
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name="chapters", verbose_name="Matière")
    
    class Meta:
        verbose_name = "Chapitre / Module"
        verbose_name_plural = "Chapitres / Modules"

    def __str__(self):
        return f"{self.matiere.name} - {self.name}"


class Sequence(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom de la séquence")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    # Field introduced to index the sequence 
    tags = models.CharField(max_length=255, blank=True, help_text="Mots-clés séparés par des virgules (ex: binaire, logique, SIN)")
    #  Fields for the "Intention" phase
    objectives = models.TextField(blank=True, null=True, verbose_name="Objectifs de la séquence")
    modalities = models.TextField(blank=True, null=True, verbose_name="Modalités et place dans la progression")
    # Other fields concerning the Sequence
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="sequences", verbose_name="Chapitre")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_sequences", verbose_name="Concepteur", null=True, blank=True)
    referee_comment = models.TextField(blank=True, null=True, verbose_name="Commentaire du référent")
    needs_second_review = models.BooleanField(default=False, verbose_name="Nécessite une seconde validation")
    first_referee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='first_reviews', verbose_name="Premier référent ayant validé")
    has_unreviewed_changes = models.BooleanField(default=False, verbose_name="Modifications non validées")

    class Meta:
        verbose_name = "Séquence"
        verbose_name_plural = "Séquences"

    def __str__(self):
        return self.name


class PlannedSession(models.Model):
    SESSION_TYPES = [
        ('COURSE', 'Cours'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
        ('EVAL', 'Évaluation'),
        ('PROJECT', 'Projet'),
    ]

    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name="planned_sessions", verbose_name="Séquence")
    order = models.IntegerField(default=1, verbose_name="Numéro")
    name = models.CharField(max_length=200, verbose_name="Titre de la séance")
    objective = models.TextField(verbose_name="Objectif de la séance", blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='COURSE', verbose_name="Type de séance")

    class Meta:
        verbose_name = "Séance prévisionnelle"
        verbose_name_plural = "Séances prévisionnelles"
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['sequence', 'order'], name='unique_planned_session_order_per_sequence')
        ]

    def __str__(self):
        return f"Séance {self.order} : {self.name}"


class Session(models.Model):
    SESSION_TYPES = [
        ('COURSE', 'Cours'),
        ('TD', 'Travaux Dirigés'),
        ('TP', 'Travaux Pratiques'),
        ('EVAL', 'Évaluation'),
        ('PROJECT', 'Projet'),
    ]

    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name="sessions", verbose_name="Séquence")
    order = models.IntegerField(default=1, verbose_name="Numéro de la séance")
    name = models.CharField(max_length=200, verbose_name="Titre de la séance")
    objective = models.TextField(verbose_name="Objectif de la séance", blank=True)
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='COURSE', verbose_name="Type de séance")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    is_essential = models.BooleanField(default=True, verbose_name="Séance essentielle", help_text="Si décoché, la séance est considérée comme facultative pour l'enseignant.")
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['sequence', 'order'], name='unique_session_order_per_sequence')
        ]

    def __str__(self):
        return f"Séance {self.order} : {self.name}"


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

    is_local = models.BooleanField(default=False, verbose_name="Activité locale", help_text="Si coché, cette activité n'apparaît que pour la classe spécifiée.")
    creator = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_activities', verbose_name="Créateur (si local)")
    classe = models.ForeignKey('classroom.Classe', on_delete=models.CASCADE, null=True, blank=True, related_name='local_activities', verbose_name="Classe concernée (si local)")
    
    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"

    def __str__(self):
        return f"{self.title} ({self.get_activity_type_display()})"


class Question(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="questions", limit_choices_to={'activity_type': 'QUIZ'}, verbose_name="Activité (Quiz)")
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