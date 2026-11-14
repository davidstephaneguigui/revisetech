"""Validation par le référent : intention, contenu, rejet, second avis."""

from unittest import expectedFailure

from django.urls import reverse

from apps.pedagogy.models import PlannedSession
from apps.review.models import ReviewAction
from apps.testing import RevisetechTestCase

JUSTIFICATION = {"reason": "ERROR", "comment": "Objectifs à préciser."}


class IntentionValidationTests(RevisetechTestCase):
    def setUp(self):
        self.sequence = self.make_sequence(status="PENDING")
        self.url = reverse("validate_sequence", args=[self.sequence.id])

    def test_get_request_is_refused(self):
        self.login(self.referee)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_referee_validates_a_pending_intention(self):
        self.login(self.referee)
        self.client.post(self.url)
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "VALIDATED")

    def test_validation_creates_sessions_from_planned_sessions(self):
        PlannedSession.objects.create(sequence=self.sequence, order=1, name="Découverte")
        PlannedSession.objects.create(
            sequence=self.sequence, order=2, name="Pratique", session_type="TP"
        )
        self.login(self.referee)
        self.client.post(self.url)
        sessions = list(self.sequence.sessions.values_list("order", "name", "session_type"))
        self.assertEqual(sessions, [(1, "Découverte", "COURSE"), (2, "Pratique", "TP")])

    def test_draft_sequence_cannot_be_validated(self):
        draft = self.make_sequence(status="DRAFT")
        self.login(self.referee)
        self.client.post(reverse("validate_sequence", args=[draft.id]))
        draft.refresh_from_db()
        self.assertEqual(draft.status, "DRAFT")

    def test_student_and_designer_cannot_validate(self):
        for user in (self.student, self.designer):
            with self.subTest(user=user.username):
                self.login(user)
                self.assertEqual(self.client.post(self.url).status_code, 403)
                self.sequence.refresh_from_db()
                self.assertEqual(self.sequence.status, "PENDING")

    def test_supervisor_validates_by_role_inheritance(self):
        """Rapport 3.4 : le superviseur hérite du rôle de référent."""
        self.login(self.supervisor)
        self.client.post(self.url)
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "VALIDATED")


class RejectionTests(RevisetechTestCase):
    def setUp(self):
        self.sequence = self.make_sequence(status="PENDING")
        self.url = reverse("reject_sequence", args=[self.sequence.id])
        self.login(self.referee)

    def test_rejection_without_comment_is_refused(self):
        self.client.post(self.url, {"reason": "ERROR", "comment": ""})
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "PENDING")
        self.assertEqual(ReviewAction.objects.count(), 0)

    def test_rejection_sends_back_to_draft_and_is_logged(self):
        self.client.post(self.url, JUSTIFICATION)
        self.sequence.refresh_from_db()
        self.assertEqual(self.sequence.status, "DRAFT")
        action = ReviewAction.objects.get()
        self.assertEqual(action.action_type, "REJECT_INTENT")
        self.assertEqual(action.user, self.referee)
        self.assertEqual(action.sequence, self.sequence)

    def test_only_pending_sequences_can_be_rejected(self):
        published = self.make_sequence(status="PUBLISHED")
        self.client.post(reverse("reject_sequence", args=[published.id]), JUSTIFICATION)
        published.refresh_from_db()
        self.assertEqual(published.status, "PUBLISHED")


class InvalidationTests(RevisetechTestCase):
    def invalidate(self, sequence, data=JUSTIFICATION):
        self.login(self.referee)
        self.client.post(reverse("invalidate_sequence", args=[sequence.id]), data)
        sequence.refresh_from_db()
        return sequence

    def test_validated_intention_goes_back_to_draft(self):
        sequence = self.invalidate(self.make_sequence(status="VALIDATED"))
        self.assertEqual(sequence.status, "DRAFT")
        self.assertEqual(ReviewAction.objects.get().action_type, "INVALIDATE_INTENT")

    def test_validated_content_goes_back_to_validated_intention(self):
        sequence = self.invalidate(self.make_sequence(status="CONTENT_VALIDATED"))
        self.assertEqual(sequence.status, "VALIDATED")
        self.assertEqual(ReviewAction.objects.get().action_type, "INVALIDATE_CONTENT")

    def test_invalidation_needs_a_comment(self):
        sequence = self.invalidate(
            self.make_sequence(status="VALIDATED"), {"reason": "OTHER", "comment": ""}
        )
        self.assertEqual(sequence.status, "VALIDATED")

    def test_published_sequence_cannot_be_invalidated(self):
        sequence = self.invalidate(self.make_sequence(status="PUBLISHED"))
        self.assertEqual(sequence.status, "PUBLISHED")
        self.assertEqual(ReviewAction.objects.count(), 0)


class ContentValidationTests(RevisetechTestCase):
    def test_designer_submits_own_content(self):
        sequence = self.make_sequence(status="VALIDATED")
        self.login(self.designer)
        self.client.post(reverse("submit_content", args=[sequence.id]))
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "CONTENT_PENDING")

    def test_designer_cannot_submit_someone_elses_content(self):
        sequence = self.make_sequence(status="VALIDATED")
        self.login(self.other_designer)
        response = self.client.post(reverse("submit_content", args=[sequence.id]))
        self.assertEqual(response.status_code, 404)

    def test_referee_validates_content_and_is_recorded(self):
        sequence = self.make_sequence(status="CONTENT_PENDING")
        self.login(self.referee)
        self.client.post(
            reverse("validate_content", args=[sequence.id]), {"referee_comment": "Très bien."}
        )
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "CONTENT_VALIDATED")
        self.assertEqual(sequence.first_referee, self.referee)
        self.assertEqual(sequence.referee_comment, "Très bien.")

    def test_draft_content_cannot_be_validated(self):
        sequence = self.make_sequence(status="DRAFT")
        self.login(self.referee)
        self.client.post(reverse("validate_content", args=[sequence.id]))
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "DRAFT")


class SecondReviewTests(RevisetechTestCase):
    def setUp(self):
        self.sequence = self.make_sequence(status="CONTENT_VALIDATED")
        self.sequence.first_referee = self.referee
        self.sequence.referee_comment = "Premier avis."
        self.sequence.needs_second_review = True
        self.sequence.save()
        self.url = reverse("validate_content", args=[self.sequence.id])

    def test_first_referee_cannot_give_the_second_opinion(self):
        self.login(self.referee)
        self.client.post(self.url, {"referee_comment": "Je confirme."})
        self.sequence.refresh_from_db()
        self.assertTrue(self.sequence.needs_second_review)
        self.assertEqual(self.sequence.referee_comment, "Premier avis.")

    def test_another_referee_gives_the_second_opinion(self):
        self.login(self.other_referee)
        self.client.post(self.url, {"referee_comment": "D'accord."})
        self.sequence.refresh_from_db()
        self.assertFalse(self.sequence.needs_second_review)
        self.assertIn("Premier avis.", self.sequence.referee_comment)
        self.assertIn("D'accord.", self.sequence.referee_comment)


class RefereePagesTests(RevisetechTestCase):
    def test_exam_page_opens_for_referee(self):
        sequence = self.make_sequence(status="CONTENT_PENDING")
        self.login(self.referee)
        response = self.client.get(reverse("referee_sequence_exam", args=[sequence.id]))
        self.assertEqual(response.status_code, 200)

    def test_exam_and_compare_pages_are_closed_to_students(self):
        sequence = self.make_sequence(status="CONTENT_PENDING")
        self.login(self.student)
        for url_name in ("referee_sequence_exam", "compare_sequences"):
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name, args=[sequence.id]))
                self.assertEqual(response.status_code, 403)

    def test_compare_search_finds_sequences_by_tag(self):
        first = self.make_sequence(name="Binaire")
        other = self.make_sequence(name="Autre séquence")
        other.tags = "logique, SIN"
        other.save()
        self.login(self.referee)
        response = self.client.get(
            reverse("compare_sequences", args=[first.id]), {"q": "logique"}
        )
        self.assertEqual(list(response.context["other_sequences"]), [other])

    @expectedFailure
    def test_chapter_detail_page_opens(self):
        """Rapport 3.10 : le template referee_chapter_detail.html n'existe pas."""
        self.login(self.referee)
        response = self.client.get(reverse("referee_chapter_detail", args=[self.chapter.id]))
        self.assertEqual(response.status_code, 200)
