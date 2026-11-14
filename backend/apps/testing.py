from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.models import User
from apps.classroom.models import Classe
from apps.pedagogy.models import Activity, Chapter, Matiere, Sequence, Session


class RevisetechTestCase(TestCase):
    def _ensure_users(self):
        """Crée les groupes et utilisateurs de base s'ils n'existent pas déjà."""
        self.group_supervisor, _ = Group.objects.get_or_create(name="Superviseur")
        self.group_referee, _ = Group.objects.get_or_create(name="Référent")
        self.group_designer, _ = Group.objects.get_or_create(name="Concepteur")
        self.group_teacher, _ = Group.objects.get_or_create(name="Enseignant")
        self.group_student, _ = Group.objects.get_or_create(name="Élève")

        if not hasattr(self, 'supervisor'):
            self.supervisor = User.objects.create_user(username="super", password="password")
            self.supervisor.groups.add(self.group_supervisor)
        
        if not hasattr(self, 'referee'):
            self.referee = User.objects.create_user(username="ref", password="password")
            self.referee.groups.add(self.group_referee)
        
        if not hasattr(self, 'designer'):
            self.designer = User.objects.create_user(username="design", password="password")
            self.designer.groups.add(self.group_designer)
        
        if not hasattr(self, 'teacher'):
            self.teacher = User.objects.create_user(username="teach", password="password")
            self.teacher.groups.add(self.group_teacher)
        
        if not hasattr(self, 'student'):
            self.student = User.objects.create_user(username="stud", password="password")
            self.student.groups.add(self.group_student)

        # --- Utilisateurs supplémentaires pour les tests avancés ---
        if not hasattr(self, 'other_designer'):
            self.other_designer = User.objects.create_user(username="design2", password="password")
            self.other_designer.groups.add(self.group_designer)
            
        if not hasattr(self, 'other_referee'):
            self.other_referee = User.objects.create_user(username="ref2", password="password")
            self.other_referee.groups.add(self.group_referee)

    def setUp(self):
        self._ensure_users()

    def _ensure_base_objects(self):
        """Crée la matière, le chapitre et la classe s'ils n'existent pas encore."""
        self._ensure_users()
        if not hasattr(self, 'matiere') or not self.matiere:
            self.matiere = Matiere.objects.create(name="Mathématiques", creator=self.designer)
        if not hasattr(self, 'chapter') or not self.chapter:
            self.chapter = Chapter.objects.create(name="Chapitre 1", matiere=self.matiere, status="DRAFT")
        if not hasattr(self, 'classe') or not self.classe:
            self.classe = Classe.objects.create(
                name="6ème A", level="6ème", specialty="Générale", main_teacher=self.teacher
            )

    def login(self, user):
        self.client.force_login(user)

    def make_sequence(self, status="DRAFT", name="Séquence de test"):
        self._ensure_base_objects()
        return Sequence.objects.create(
            name=name, 
            chapter=self.chapter, 
            creator=self.designer, 
            status=status
        )

    def make_session(self, sequence, order=1, name="Séance 1"):
        self._ensure_users()
        return Session.objects.create(
            sequence=sequence, 
            order=order,
            name=name, 
            objective="Objectif de test", 
            status="DRAFT"
        )

    def make_quiz(self, session, title="Quiz de test"):
        self._ensure_users()
        quiz = Activity.objects.create(
            title=title, 
            activity_type="QUIZ", 
            status="DRAFT"
        )
        quiz.sessions.add(session)
        return quiz

    def make_published_quiz(self):
        seq = self.make_sequence(status="PUBLISHED")
        ses = self.make_session(seq)
        ses.status = "PUBLISHED"
        ses.save()
        quiz = self.make_quiz(ses)
        quiz.status = "PUBLISHED"
        quiz.save()
        return seq, ses, quiz
