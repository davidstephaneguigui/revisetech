"""Espace enseignant : classes, préparation des séances, suivi des élèves."""

from unittest import expectedFailure

from django.urls import reverse

from apps.classroom.models import (
    ActivitySelection,
    Classe,
    SessionCompletion,
    Suggestion,
)
from apps.classroom.utils import compute_sequence_stats, get_student_global_score
from apps.learning.models import Result
from apps.pedagogy.models import Activity, Choice, Question
from apps.testing import RevisetechTestCase


class ClassTests(RevisetechTestCase):
    def test_teacher_creates_a_class_with_an_invitation_code(self):
        self.login(self.teacher)
        self.client.post(
            reverse("teacher_dashboard"),
            {"name": "1re B", "level": "Première", "specialty": "STI2D"},
        )
        classe = Classe.objects.get(name="1re B")
        self.assertEqual(classe.main_teacher, self.teacher)
        self.assertEqual(len(classe.code_invitation), 8)

    def test_invitation_codes_are_different(self):
        other = Classe.objects.create(
            name="2nde B", level="Seconde", specialty="SNT", main_teacher=self.teacher
        )
        self.assertNotEqual(other.code_invitation, self.classe.code_invitation)

    def test_teacher_cannot_open_another_teachers_class(self):
        self.login(self.other_teacher)
        for url_name in ("class_detail", "class_results"):
            with self.subTest(page=url_name):
                response = self.client.get(reverse(url_name, args=[self.classe.id]))
                self.assertEqual(response.status_code, 404)

    def test_student_joins_a_class_with_its_code(self):
        self.login(self.outsider)
        self.client.post(
            reverse("join_class"), {"code_invitation": self.classe.code_invitation.lower()}
        )
        self.assertIn(self.outsider, self.classe.students.all())

    def test_wrong_code_does_not_join_any_class(self):
        self.login(self.outsider)
        response = self.client.post(reverse("join_class"), {"code_invitation": "FAUXCODE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.outsider.student_classes.count(), 0)

    def test_teacher_assigns_a_published_sequence_to_the_class(self):
        sequence = self.make_sequence(status="PUBLISHED")
        self.login(self.teacher)
        self.client.post(
            reverse("class_detail", args=[self.classe.id]),
            {"add_sequences": "1", "sequences": [sequence.id]},
        )
        self.assertIn(sequence, self.classe.sequences.all())

    def test_teacher_cannot_assign_an_unpublished_sequence(self):
        sequence = self.make_sequence(status="DRAFT")
        self.login(self.teacher)
        self.client.post(
            reverse("class_detail", args=[self.classe.id]),
            {"add_sequences": "1", "sequences": [sequence.id]},
        )
        self.assertNotIn(sequence, self.classe.sequences.all())

    @expectedFailure
    def test_teacher_cannot_add_a_staff_account_as_student(self):
        """Rapport 2.5 : n'importe quel compte peut être ajouté à une classe par son identifiant."""
        self.login(self.teacher)
        self.client.post(
            reverse("class_detail", args=[self.classe.id]),
            {"add_student": "1", "username": self.other_teacher.username},
        )
        self.assertNotIn(self.other_teacher, self.classe.students.all())


class SessionPreparationTests(RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz()
        self.login(self.teacher)

    def test_prepare_page_opens_and_lists_the_activities(self):
        response = self.client.get(
            reverse("prepare_session", args=[self.classe.id, self.session.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["all_activities"], [self.quiz])

    def test_toggling_a_session_marks_it_done_then_not_done(self):
        url = reverse("toggle_session_completion", args=[self.classe.id, self.session.id])
        self.assertTrue(self.client.post(url).json()["is_completed"])
        self.assertFalse(self.client.post(url).json()["is_completed"])
        self.assertEqual(SessionCompletion.objects.count(), 1)

    def test_toggling_an_activity_hides_it_from_students(self):
        url = reverse("toggle_activity_usage", args=[self.classe.id, self.quiz.id])
        self.assertFalse(self.client.post(url).json()["is_used"])
        self.login(self.student)
        response = self.client.get(reverse("activity_detail", args=[self.quiz.id]))
        self.assertEqual(response.status_code, 404)

    def test_other_teacher_cannot_change_the_preparation(self):
        self.login(self.other_teacher)
        url = reverse("toggle_activity_usage", args=[self.classe.id, self.quiz.id])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(ActivitySelection.objects.get(activity=self.quiz).is_used)

    def test_teacher_creates_a_local_activity_for_the_class(self):
        self.client.post(
            reverse("create_local_activity", args=[self.classe.id, self.session.id]),
            {"title": "Rappel de cours", "activity_type": "COURSE", "content": "…"},
        )
        local = Activity.objects.get(title="Rappel de cours")
        self.assertTrue(local.is_local)
        self.assertEqual((local.classe, local.creator), (self.classe, self.teacher))

    def test_moving_an_activity_changes_the_order_for_the_class_only(self):
        second = self.make_quiz(self.session, status="PUBLISHED", title="Second quiz")
        self.client.post(
            reverse("move_activity", args=[self.classe.id, self.session.id, second.id, "up"])
        )
        response = self.client.get(
            reverse("prepare_session", args=[self.classe.id, self.session.id])
        )
        self.assertEqual(response.context["all_activities"], [second, self.quiz])

    @expectedFailure
    def test_draft_activity_cannot_be_cloned_as_published(self):
        """Rapport 2.4 : cloner une activité en brouillon crée une copie publiée."""
        draft = self.make_quiz(self.make_session(self.make_sequence()), title="Non validé")
        self.client.post(
            reverse("add_existing_activity", args=[self.classe.id, self.session.id]),
            {"global_activity_id": draft.id},
        )
        self.assertFalse(Activity.objects.filter(is_local=True, status="PUBLISHED").exists())

    @expectedFailure
    def test_cloned_quiz_keeps_its_questions(self):
        """Rapport 3.5 : la copie d'un quiz ne reprend pas ses questions."""
        self.client.post(
            reverse("add_existing_activity", args=[self.classe.id, self.session.id]),
            {"global_activity_id": self.quiz.id},
        )
        copy = Activity.objects.get(is_local=True)
        self.assertEqual(copy.questions.count(), self.quiz.questions.count())


class StudentFollowUpTests(RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz(questions=2)

    def test_teacher_opens_the_profile_of_own_student(self):
        self.login(self.teacher)
        response = self.client.get(reverse("student_profile", args=[self.student.id]))
        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_open_the_profile_of_another_class_student(self):
        self.login(self.teacher)
        response = self.client.get(reverse("student_profile", args=[self.outsider.id]))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_read_another_students_results(self):
        self.login(self.outsider)
        response = self.client.get(reverse("student_results", args=[self.student.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_teacher_sends_a_suggestion_to_own_student(self):
        self.login(self.teacher)
        self.client.post(
            reverse("student_results", args=[self.student.id]),
            {"activity": self.quiz.id, "message": "À revoir avant le contrôle."},
        )
        suggestion = Suggestion.objects.get()
        self.assertEqual((suggestion.teacher, suggestion.student), (self.teacher, self.student))
        self.assertFalse(suggestion.is_read)

    def test_suggestion_list_marks_everything_read(self):
        Suggestion.objects.create(teacher=self.teacher, student=self.student, activity=self.quiz)
        self.login(self.student)
        self.client.get(reverse("suggestion_list"))
        self.assertFalse(Suggestion.objects.filter(is_read=False).exists())


class StatisticsTests(RevisetechTestCase):
    def setUp(self):
        self.sequence, self.session, self.quiz = self.make_published_quiz(questions=2)

    def result(self, student, score):
        return Result.objects.create(student=student, activity=self.quiz, score=score, max_score=2)

    def test_student_without_result_has_no_score(self):
        self.assertEqual(get_student_global_score(self.student), (None, "secondary"))

    def test_global_score_is_on_twenty(self):
        self.result(self.student, 1)
        score, _ = get_student_global_score(self.student)
        self.assertEqual(score, 10.0)

    def test_sequence_stats_give_mean_min_max_and_count(self):
        self.result(self.student, 2)
        self.result(self.outsider, 1)
        self.assertEqual(compute_sequence_stats(self.sequence), (15.0, 10.0, 20.0, 2))

    def test_sequence_stats_can_be_limited_to_a_class(self):
        self.result(self.student, 2)
        self.result(self.outsider, 0)
        self.assertEqual(compute_sequence_stats(self.sequence, self.classe), (20.0, 20.0, 20.0, 1))

    def test_sequence_without_result_has_empty_stats(self):
        self.assertEqual(compute_sequence_stats(self.sequence), (None, None, None, 0))

    @expectedFailure
    def test_score_does_not_change_when_a_question_is_added_later(self):
        """Rapport 3.8 : le score utilise le nombre actuel de questions, pas max_score."""
        self.result(self.student, 1)  # 1 sur 2 le jour de la tentative
        extra = Question.objects.create(activity=self.quiz, text="Ajoutée après", order=3)
        Choice.objects.create(question=extra, text="oui", is_correct=True)
        score, _ = get_student_global_score(self.student)
        self.assertEqual(score, 10.0)

