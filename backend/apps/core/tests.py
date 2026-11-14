"""Accueil commun, aide, statistiques générales et réglages de sécurité."""

from unittest import expectedFailure

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse

from apps.learning.models import Result
from apps.testing import RevisetechTestCase


class DashboardHomeTests(RevisetechTestCase):
    def test_each_role_gets_its_own_dashboard(self):
        expected = {
            "teacher": "Enseignant",
            "designer": "Concepteur",
            "referee": "Référent",
            "supervisor": "Superviseur",
        }
        for attribute, role in expected.items():
            with self.subTest(role=role):
                self.login(getattr(self, attribute))
                response = self.client.get(reverse("dashboard_home"))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["role"], role)

    def test_student_is_sent_to_the_student_home(self):
        self.login(self.student)
        response = self.client.get(reverse("dashboard_home"))
        self.assertRedirects(response, reverse("student_home"))

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse("dashboard_home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_designer_counters_only_count_own_sequences(self):
        self.make_sequence(status="DRAFT")
        self.make_sequence(status="PUBLISHED")
        self.make_sequence(status="PUBLISHED", creator=self.other_designer)
        self.login(self.designer)
        context = self.client.get(reverse("dashboard_home")).context
        self.assertEqual(context["intentions_count"], 1)
        self.assertEqual(context["published_count"], 1)

    def test_teacher_counters_only_count_own_classes(self):
        self.login(self.teacher)
        context = self.client.get(reverse("dashboard_home")).context
        self.assertEqual((context["classes_count"], context["students_count"]), (1, 1))
        self.login(self.other_teacher)
        context = self.client.get(reverse("dashboard_home")).context
        self.assertEqual((context["classes_count"], context["students_count"]), (0, 0))

    def test_help_page_adapts_to_the_role(self):
        for user, role in ((self.student, "Élève"), (self.referee, "Référent")):
            with self.subTest(role=role):
                self.login(user)
                response = self.client.get(reverse("help_page"))
                self.assertEqual(response.context["role"], role)


class GlobalStatisticsTests(RevisetechTestCase):
    def test_referee_sees_the_statistics(self):
        _, _, quiz = self.make_published_quiz()
        Result.objects.create(student=self.student, activity=quiz, score=1, max_score=2)
        self.login(self.referee)
        response = self.client.get(reverse("apprenticeship_stats"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_results"], 1)
        self.assertEqual(response.context["active_students"], 1)

    def test_students_and_teachers_do_not_see_the_statistics(self):
        for user in (self.student, self.teacher):
            with self.subTest(user=user.username):
                self.login(user)
                response = self.client.get(reverse("apprenticeship_stats"))
                self.assertNotEqual(response.status_code, 200)


class SettingsTests(SimpleTestCase):
    @expectedFailure
    def test_secret_key_is_not_the_one_published_in_the_repository(self):
        """Rapport 2.6 : la clé secrète est écrite en clair dans settings.py."""
        self.assertFalse(settings.SECRET_KEY.startswith("django-insecure-"))

