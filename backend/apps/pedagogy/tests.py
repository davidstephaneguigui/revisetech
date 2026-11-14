"""Consultation des contenus : ce que l'élève voit, intégrité des données."""

from unittest import expectedFailure

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from apps.classroom.models import ActivitySelection, Classe, Suggestion
from apps.pedagogy.models import Activity, Sequence, Session
from apps.testing import RevisetechTestCase


class StudentVisibilityTests(RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz()
        self.draft = self.make_sequence(status="DRAFT", name="Brouillon")
        self.draft_session = self.make_session(self.draft)
        self.draft_quiz = self.make_quiz(self.draft_session)
        self.login(self.student)

    def test_published_content_is_visible(self):
        pages = {
            "sequence_detail": self.sequence,
            "session_detail": self.session,
            "activity_detail": self.quiz,
        }
        for url_name, item in pages.items():
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name, args=[item.id]))
                self.assertEqual(response.status_code, 200)

    def test_unpublished_content_is_hidden(self):
        pages = {
            "sequence_detail": self.draft,
            "session_detail": self.draft_session,
            "activity_detail": self.draft_quiz,
        }
        for url_name, item in pages.items():
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name, args=[item.id]))
                self.assertEqual(response.status_code, 404)

    def test_sequence_page_lists_only_published_sessions(self):
        self.make_session(self.sequence, order=2, status="DRAFT")
        response = self.client.get(reverse("sequence_detail", args=[self.sequence.id]))
        self.assertEqual(list(response.context["sessions"]), [self.session])

    def test_activity_not_selected_by_the_teacher_is_hidden(self):
        ActivitySelection.objects.filter(activity=self.quiz).update(is_used=False)
        response = self.client.get(reverse("activity_detail", args=[self.quiz.id]))
        self.assertEqual(response.status_code, 404)
        session_page = self.client.get(reverse("session_detail", args=[self.session.id]))
        self.assertEqual(list(session_page.context["activities"]), [])

    def test_local_activity_is_visible_only_to_its_class(self):
        other_class = Classe.objects.create(
            name="2nde B", level="Seconde", specialty="SNT", main_teacher=self.other_teacher
        )
        for classe, expected in ((self.classe, 200), (other_class, 404)):
            with self.subTest(classe=classe.name):
                local = Activity.objects.create(
                    title=f"Locale {classe.name}",
                    activity_type="EXERCISE",
                    status="PUBLISHED",
                    is_local=True,
                    classe=classe,
                )
                local.sessions.add(self.session)
                response = self.client.get(reverse("activity_detail", args=[local.id]))
                self.assertEqual(response.status_code, expected)

    def test_teacher_can_read_unpublished_content(self):
        self.login(self.teacher)
        response = self.client.get(reverse("activity_detail", args=[self.draft_quiz.id]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_sent_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("sequence_detail", args=[self.sequence.id]))
        self.assertEqual(response.status_code, 302)

    @expectedFailure
    def test_published_sequence_is_reachable_in_a_partly_published_chapter(self):
        """Rapport 3.1 : le chapitre reste caché tant qu'une de ses séquences n'est pas publiée."""
        subject_page = self.client.get(reverse("subject_detail", args=[self.subject.id]))
        self.assertIn(self.chapter, subject_page.context["chapters"])
        chapter_page = self.client.get(reverse("chapter_detail", args=[self.chapter.id]))
        self.assertEqual(chapter_page.status_code, 200)
        self.assertEqual(list(chapter_page.context["sequences"]), [self.sequence])


class SuggestionReadTests(RevisetechTestCase):
    def setUp(self):
        _, _, self.quiz = self.make_published_quiz()
        self.suggestion = Suggestion.objects.create(
            teacher=self.teacher, student=self.student, activity=self.quiz
        )
        self.url = reverse("mark_suggestion_read", args=[self.suggestion.id])

    def test_opening_a_suggestion_marks_it_read_and_goes_to_the_activity(self):
        self.login(self.student)
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("activity_detail", args=[self.quiz.id]),
            fetch_redirect_response=False,
        )
        self.suggestion.refresh_from_db()
        self.assertTrue(self.suggestion.is_read)

    def test_another_student_cannot_open_the_suggestion(self):
        self.login(self.outsider)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.suggestion.refresh_from_db()
        self.assertFalse(self.suggestion.is_read)


class DataIntegrityTests(RevisetechTestCase):
    def test_two_sessions_cannot_share_a_number_in_a_sequence(self):
        sequence = self.make_sequence()
        self.make_session(sequence, order=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Session.objects.create(sequence=sequence, order=1, name="Doublon")

    def test_same_number_is_allowed_in_two_sequences(self):
        self.make_session(self.make_sequence(name="A"), order=1)
        self.make_session(self.make_sequence(name="B"), order=1)
        self.assertEqual(Session.objects.filter(order=1).count(), 2)

    def test_new_sequence_starts_as_draft(self):
        self.assertEqual(self.make_sequence().status, "DRAFT")

    @expectedFailure
    def test_deleting_a_designer_keeps_the_sequences(self):
        """Rapport 1 (point du 7 novembre) : CASCADE sur le créateur supprime ses contenus."""
        sequence = self.make_sequence(status="PUBLISHED")
        try:
            self.designer.delete()
        except ProtectedError:
            pass  # PROTECT est une correction acceptable
        self.assertTrue(Sequence.objects.filter(id=sequence.id).exists())

