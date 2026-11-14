"""Publication par le superviseur : publier, dépublier, demander un second avis."""

from unittest import expectedFailure

from django.urls import reverse

from apps.pedagogy.models import Activity
from apps.testing import RevisetechTestCase


class PublishTests(RevisetechTestCase):
    def setUp(self):
        self.sequence = self.make_sequence(status="CONTENT_VALIDATED")
        self.session = self.make_session(self.sequence)
        self.quiz = self.make_quiz(self.session)
        self.url = reverse("publish_sequence", args=[self.sequence.id])

    def test_supervisor_publishes_sequence_sessions_and_activities(self):
        self.login(self.supervisor)
        self.client.post(self.url)
        for item in (self.sequence, self.session, self.quiz):
            item.refresh_from_db()
            self.assertEqual(item.status, "PUBLISHED")

    def test_chapter_is_published_when_all_its_sequences_are(self):
        self.login(self.supervisor)
        self.client.post(self.url)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.status, "PUBLISHED")

    def test_chapter_stays_unpublished_while_a_sequence_is_missing(self):
        self.make_sequence(status="DRAFT", name="Pas prête")
        self.login(self.supervisor)
        self.client.post(self.url)
        self.chapter.refresh_from_db()
        self.assertNotEqual(self.chapter.status, "PUBLISHED")

    def test_get_request_is_refused(self):
        self.login(self.supervisor)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_referee_cannot_publish(self):
        self.login(self.referee)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "CONTENT_VALIDATED")

    def test_content_not_validated_cannot_be_published(self):
        pending = self.make_sequence(status="CONTENT_PENDING")
        self.login(self.supervisor)
        self.client.post(reverse("publish_sequence", args=[pending.id]))
        pending.refresh_from_db()
        self.assertEqual(pending.status, "CONTENT_PENDING")

    def test_supervisor_requests_a_second_review(self):
        self.login(self.supervisor)
        self.client.post(reverse("request_second_review", args=[self.sequence.id]))
        self.sequence.refresh_from_db()
        self.assertTrue(self.sequence.needs_second_review)
        self.assertEqual(self.sequence.status, "CONTENT_VALIDATED")


class UnpublishTests(RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz()
        self.chapter.status = "PUBLISHED"
        self.chapter.save()
        self.url = reverse("unpublish_sequence", args=[self.sequence.id])

    def test_supervisor_unpublishes(self):
        self.login(self.supervisor)
        self.client.post(self.url)
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "CONTENT_VALIDATED")

    def test_student_cannot_unpublish(self):
        """Rapport 2.1 : unpublish_sequence n'a pas de contrôle de rôle."""
        self.login(self.student)
        response = self.client.post(self.url)
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "PUBLISHED")
        self.assertEqual(response.status_code, 403)

    @expectedFailure
    def test_unpublishing_keeps_teachers_local_activities(self):
        """Rapport 3.6 : la dépublication repasse aussi les activités locales en brouillon."""
        local = Activity.objects.create(
            title="Activité de l'enseignant",
            activity_type="EXERCISE",
            status="PUBLISHED",
            is_local=True,
            creator=self.teacher,
            classe=self.classe,
        )
        local.sessions.add(self.session)
        self.login(self.supervisor)
        self.client.post(self.url)
        local.refresh_from_db()
        self.assertEqual(local.status, "PUBLISHED")

    @expectedFailure
    def test_unpublishing_also_unpublishes_the_chapter(self):
        """Rapport 3.6 : le chapitre reste « publié » sans aucune séquence publiée."""
        self.login(self.supervisor)
        self.client.post(self.url)
        self.chapter.refresh_from_db()
        self.assertNotEqual(self.chapter.status, "PUBLISHED")


class SupervisorPagesTests(RevisetechTestCase):
    def setUp(self):
        self.draft = self.make_sequence(status="DRAFT", name="Brouillon confidentiel")

    def test_exam_page_opens_for_supervisor(self):
        self.login(self.supervisor)
        response = self.client.get(reverse("supervisor_sequence_exam", args=[self.draft.id]))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_read_a_draft_through_the_exam_page(self):
        """Rapport 2.2 : supervisor_sequence_exam n'a pas de contrôle de rôle."""
        self.login(self.student)
        response = self.client.get(reverse("supervisor_sequence_exam", args=[self.draft.id]))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_see_sequence_statistics(self):
        self.login(self.student)
        response = self.client.get(reverse("sequence_stats", args=[self.draft.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_teacher_sees_sequence_statistics(self):
        self.login(self.teacher)
        response = self.client.get(reverse("sequence_stats", args=[self.draft.id]))
        self.assertEqual(response.status_code, 200)

