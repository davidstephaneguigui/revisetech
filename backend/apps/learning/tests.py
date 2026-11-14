"""Espace élève : accueil, correction des quiz par l'API, badges."""

import json
from unittest import expectedFailure

from django.urls import reverse

from apps.learning.models import Badge, Result
from apps.testing import RevisetechTestCase


class QuizApiMixin:
    def submit(self, quiz, answers):
        return self.client.post(
            reverse("api_submit_quiz", args=[quiz.id]),
            data=json.dumps({"answers": answers}),
            content_type="application/json",
        )


class QuizScoringTests(QuizApiMixin, RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz(questions=4)
        self.login(self.student)

    def test_all_correct_answers_give_the_full_score(self):
        response = self.submit(self.quiz, self.answers(self.quiz))
        self.assertEqual(
            response.json(), {"status": "success", "score": 4, "max_score": 4}
        )

    def test_score_counts_only_correct_answers(self):
        response = self.submit(self.quiz, self.answers(self.quiz, correct=1))
        self.assertEqual(response.json()["score"], 1)

    def test_missing_answers_count_as_wrong(self):
        self.assertEqual(self.submit(self.quiz, {}).json()["score"], 0)

    def test_choice_from_another_question_is_ignored(self):
        first, second = list(self.quiz.questions.all())[:2]
        foreign_choice = second.choices.get(is_correct=True)
        response = self.submit(self.quiz, {str(first.id): foreign_choice.id})
        self.assertEqual(response.json()["score"], 0)

    def test_result_is_saved_for_the_student(self):
        self.submit(self.quiz, self.answers(self.quiz, correct=3))
        result = Result.objects.get()
        self.assertEqual(
            (result.student, result.activity, result.score, result.max_score),
            (self.student, self.quiz, 3, 4),
        )

    def test_get_request_is_refused(self):
        response = self.client.get(reverse("api_submit_quiz", args=[self.quiz.id]))
        self.assertEqual(response.status_code, 405)

    def test_anonymous_user_cannot_submit(self):
        self.client.logout()
        response = self.submit(self.quiz, self.answers(self.quiz))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Result.objects.count(), 0)

    def test_correct_answers_are_not_sent_to_the_browser(self):
        response = self.client.get(reverse("activity_detail", args=[self.quiz.id]))
        self.assertEqual(response.status_code, 200)
        for question in response.context["quiz_data"]:
            for choice in question["choices"]:
                self.assertEqual(set(choice), {"id", "text"})
        self.assertNotContains(response, "is_correct")


class QuizAccessTests(QuizApiMixin, RevisetechTestCase):
    @expectedFailure
    def test_student_cannot_submit_a_draft_quiz(self):
        """Rapport 2.3 : l'API n'applique pas les règles d'accès de la page du quiz."""
        draft = self.make_sequence(status="DRAFT")
        quiz = self.make_quiz(self.make_session(draft))
        self.login(self.student)
        response = self.submit(quiz, self.answers(quiz))
        self.assertEqual(Result.objects.count(), 0)
        self.assertIn(response.status_code, (403, 404))

    @expectedFailure
    def test_student_cannot_submit_a_quiz_of_another_class(self):
        """Rapport 2.3 : un élève hors de la classe peut enregistrer un résultat."""
        _, _, quiz = self.make_published_quiz()
        self.login(self.outsider)
        self.submit(quiz, self.answers(quiz))
        self.assertEqual(Result.objects.count(), 0)

    @expectedFailure
    def test_error_response_does_not_leak_python_messages(self):
        """Rapport 2.3 : le message d'exception brut est renvoyé au navigateur."""
        _, _, quiz = self.make_published_quiz()
        self.login(self.student)
        response = self.client.post(
            reverse("api_submit_quiz", args=[quiz.id]),
            data="{json invalide",
            content_type="application/json",
        )
        self.assertNotIn("Expecting", response.json()["message"])


class BadgeTests(QuizApiMixin, RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz(questions=10)
        self.login(self.student)

    def test_badge_is_awarded_from_70_percent(self):
        self.submit(self.quiz, self.answers(self.quiz, correct=7))
        self.assertTrue(Badge.objects.filter(student=self.student, sequence=self.sequence).exists())

    def test_no_badge_below_70_percent(self):
        self.submit(self.quiz, self.answers(self.quiz, correct=6))
        self.assertFalse(Badge.objects.exists())

    def test_badge_needs_every_quiz_of_the_sequence(self):
        self.make_quiz(self.session, status="PUBLISHED", title="Second quiz")
        self.submit(self.quiz, self.answers(self.quiz))
        self.assertFalse(Badge.objects.exists())

    def test_badge_is_kept_after_a_weaker_new_attempt(self):
        self.submit(self.quiz, self.answers(self.quiz, correct=9))
        self.submit(self.quiz, self.answers(self.quiz, correct=2))
        self.assertEqual(Badge.objects.count(), 1)

    def test_badge_is_given_only_once(self):
        self.submit(self.quiz, self.answers(self.quiz))
        self.submit(self.quiz, self.answers(self.quiz))
        self.assertEqual(Badge.objects.count(), 1)


class StudentHomeTests(RevisetechTestCase):
    def test_home_lists_subjects_of_sequences_assigned_to_the_class(self):
        self.make_published_quiz()
        self.login(self.student)
        response = self.client.get(reverse("student_home"))
        self.assertEqual(list(response.context["subjects"]), [self.subject])

    def test_home_hides_subjects_when_nothing_is_assigned(self):
        self.make_published_quiz(assign=False)
        self.login(self.student)
        response = self.client.get(reverse("student_home"))
        self.assertEqual(list(response.context["subjects"]), [])

    def test_home_hides_assigned_but_unpublished_sequences(self):
        self.classe.sequences.add(self.make_sequence(status="CONTENT_VALIDATED"))
        self.login(self.student)
        response = self.client.get(reverse("student_home"))
        self.assertEqual(list(response.context["subjects"]), [])

    def test_progression_counts_the_sequences_of_the_class(self):
        self.make_published_quiz()
        self.login(self.student)
        response = self.client.get(reverse("student_progression"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_sequences"], 1)

