"""Atelier du concepteur : séquences, séances, quiz, propositions d'activités."""

import tempfile
from unittest import expectedFailure

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.authoring.models import ActivityProposal
from apps.pedagogy.models import Activity, Sequence, Session
from apps.testing import RevisetechTestCase

INTENTION = {
    "tags": "binaire, logique",
    "objectives": "Convertir un nombre du décimal vers le binaire.",
    "modalities": "Deux séances en début d'année.",
    # Formulaires des séances prévisionnelles : aucun ici
    "planned_sessions-TOTAL_FORMS": "0",
    "planned_sessions-INITIAL_FORMS": "0",
}


class SequenceTests(RevisetechTestCase):
    def test_designer_creates_a_draft_sequence(self):
        self.login(self.designer)
        self.client.post(
            reverse("designer_dashboard"), {"name": "Codage", "chapter": self.chapter.id}
        )
        sequence = Sequence.objects.get(name="Codage")
        self.assertEqual(sequence.creator, self.designer)
        self.assertEqual(sequence.status, "DRAFT")

    def test_designer_cannot_open_someone_elses_sequence(self):
        sequence = self.make_sequence(creator=self.other_designer)
        self.login(self.designer)
        response = self.client.get(reverse("manage_sequence", args=[sequence.id]))
        self.assertEqual(response.status_code, 404)

    def test_saving_the_intention_keeps_the_draft_status(self):
        sequence = self.make_sequence()
        self.login(self.designer)
        self.client.post(
            reverse("manage_sequence", args=[sequence.id]), {**INTENTION, "save_intention": "1"}
        )
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "DRAFT")
        self.assertEqual(sequence.tags, "binaire, logique")

    def test_submitting_the_intention_sends_it_to_the_referee(self):
        sequence = self.make_sequence()
        self.login(self.designer)
        self.client.post(
            reverse("manage_sequence", args=[sequence.id]),
            {**INTENTION, "submit_intention": "1"},
        )
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "PENDING")

    def test_intention_without_objectives_is_not_submitted(self):
        sequence = self.make_sequence()
        self.login(self.designer)
        self.client.post(
            reverse("manage_sequence", args=[sequence.id]),
            {**INTENTION, "objectives": "", "submit_intention": "1"},
        )
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "DRAFT")

    @expectedFailure
    def test_published_sequence_cannot_be_resubmitted_as_intention(self):
        """Rapport 3.3 : une séquence publiée peut être renvoyée en PENDING."""
        sequence = self.make_sequence(status="PUBLISHED")
        self.login(self.designer)
        self.client.post(
            reverse("manage_sequence", args=[sequence.id]),
            {**INTENTION, "submit_intention": "1"},
        )
        sequence.refresh_from_db()
        self.assertEqual(sequence.status, "PUBLISHED")

    def test_draft_sequence_can_be_deleted(self):
        sequence = self.make_sequence()
        self.login(self.designer)
        self.client.post(reverse("delete_sequence", args=[sequence.id]))
        self.assertFalse(Sequence.objects.filter(id=sequence.id).exists())

    def test_sequence_under_review_cannot_be_deleted(self):
        sequence = self.make_sequence(status="PENDING")
        self.login(self.designer)
        self.client.post(reverse("delete_sequence", args=[sequence.id]))
        self.assertTrue(Sequence.objects.filter(id=sequence.id).exists())


class SessionTests(RevisetechTestCase):
    def setUp(self):
        self.sequence = self.make_sequence(status="VALIDATED")
        self.first = self.make_session(self.sequence, order=1)
        self.second = self.make_session(self.sequence, order=2)
        self.third = self.make_session(self.sequence, order=3)
        self.login(self.designer)

    def test_adding_a_session_takes_the_next_number_and_flags_the_sequence(self):
        self.client.post(
            reverse("manage_sequence", args=[self.sequence.id]),
            {"add_session": "1", "name": "Bilan", "objective": ""},
        )
        self.assertEqual(Session.objects.get(name="Bilan").order, 4)
        self.sequence.refresh_from_db()
        self.assertTrue(self.sequence.has_unreviewed_changes)

    def test_deleting_a_session_renumbers_the_others(self):
        self.client.post(reverse("delete_session", args=[self.first.id]))
        orders = list(self.sequence.sessions.values_list("name", "order"))
        self.assertEqual(orders, [("Séance 2", 1), ("Séance 3", 2)])

    def test_validated_session_cannot_be_deleted(self):
        self.first.status = "PUBLISHED"
        self.first.save()
        self.client.post(reverse("delete_session", args=[self.first.id]))
        self.assertTrue(Session.objects.filter(id=self.first.id).exists())

    def test_other_designer_cannot_delete_a_session(self):
        self.login(self.other_designer)
        response = self.client.post(reverse("delete_session", args=[self.first.id]))
        self.assertEqual(response.status_code, 404)

    @expectedFailure
    def test_moving_a_session_swaps_it_with_its_neighbour(self):
        """Rapport 3.2 : l'échange des numéros enfreint la contrainte d'unicité."""
        self.client.post(reverse("move_session", args=[self.second.id, "up"]))
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual((self.second.order, self.first.order), (1, 2))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="revisetech-tests-"))
class ActivityAndQuizTests(RevisetechTestCase):
    def setUp(self):
        self.sequence = self.make_sequence(status="VALIDATED")
        self.session = self.make_session(self.sequence)
        self.login(self.designer)

    def test_designer_adds_an_activity_to_a_session(self):
        self.client.post(
            reverse("manage_session", args=[self.session.id]),
            {"title": "Cours sur le binaire", "activity_type": "COURSE", "content": "…"},
        )
        activity = Activity.objects.get(title="Cours sur le binaire")
        self.assertEqual(list(activity.sessions.all()), [self.session])
        self.assertEqual(activity.status, "DRAFT")

    def test_designer_adds_a_question_with_its_choices(self):
        quiz = self.make_quiz(self.session, questions=0)
        self.client.post(
            reverse("manage_quiz_questions", args=[quiz.id]),
            {
                "text": "Combien vaut 101 en binaire ?",
                "order": 1,
                "choice_1": "5",
                "choice_2": "3",
                "choice_3": "",
                "choice_4": "",
                "correct_choice": "1",
            },
        )
        question = quiz.questions.get()
        self.assertEqual(question.choices.count(), 2)
        self.assertEqual(question.choices.get(is_correct=True).text, "5")

    def test_other_designer_cannot_edit_the_quiz(self):
        quiz = self.make_quiz(self.session)
        self.login(self.other_designer)
        response = self.client.get(reverse("manage_quiz_questions", args=[quiz.id]))
        self.assertEqual(response.status_code, 404)

    def test_designer_deletes_a_question(self):
        quiz = self.make_quiz(self.session, questions=2)
        self.client.post(reverse("delete_question", args=[quiz.questions.first().id]))
        self.assertEqual(quiz.questions.count(), 1)

    @expectedFailure
    def test_html_file_upload_is_refused(self):
        """Rapport 2.6 : le type des fichiers envoyés n'est pas contrôlé."""
        page = SimpleUploadedFile(
            "piege.html", b"<script>alert(1)</script>", content_type="text/html"
        )
        self.client.post(
            reverse("manage_session", args=[self.session.id]),
            {"title": "Fichier piégé", "activity_type": "COURSE", "file_upload": page},
        )
        self.assertFalse(Activity.objects.filter(title="Fichier piégé").exists())

    @expectedFailure
    def test_editing_a_published_activity_flags_the_sequence_for_review(self):
        """Rapport 3.9 : un contenu publié se modifie sans nouvelle relecture."""
        sequence, session, quiz = self.make_published_quiz()
        self.client.post(
            reverse("edit_activity", args=[quiz.id]),
            {"title": "Titre modifié après publication", "activity_type": "QUIZ"},
        )
        sequence.refresh_from_db()
        self.assertTrue(sequence.has_unreviewed_changes)


class ProposalTests(RevisetechTestCase):
    def setUp(self):
        sequence, self.session, _ = self.make_published_quiz()
        self.local = Activity.objects.create(
            title="Exercice maison",
            activity_type="EXERCISE",
            status="PUBLISHED",
            is_local=True,
            creator=self.teacher,
            classe=self.classe,
        )
        self.local.sessions.add(self.session)

    def test_teacher_proposes_own_local_activity(self):
        self.login(self.teacher)
        self.client.post(reverse("propose_activity", args=[self.local.id]))
        proposal = ActivityProposal.objects.get()
        self.assertEqual((proposal.teacher, proposal.status), (self.teacher, "PENDING"))

    def test_same_activity_is_not_proposed_twice(self):
        self.login(self.teacher)
        self.client.post(reverse("propose_activity", args=[self.local.id]))
        self.client.post(reverse("propose_activity", args=[self.local.id]))
        self.assertEqual(ActivityProposal.objects.count(), 1)

    def test_teacher_cannot_propose_someone_elses_activity(self):
        self.login(self.other_teacher)
        self.client.post(reverse("propose_activity", args=[self.local.id]))
        self.assertEqual(ActivityProposal.objects.count(), 0)

    def test_teacher_cannot_accept_a_proposal(self):
        proposal = ActivityProposal.objects.create(activity=self.local, teacher=self.teacher)
        self.login(self.teacher)
        self.client.post(reverse("handle_proposal", args=[proposal.id, "accept"]))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "PENDING")

    def test_designer_rejects_a_proposal(self):
        proposal = ActivityProposal.objects.create(activity=self.local, teacher=self.teacher)
        self.login(self.designer)
        self.client.post(reverse("handle_proposal", args=[proposal.id, "reject"]))
        proposal.refresh_from_db()
        self.local.refresh_from_db()
        self.assertEqual(proposal.status, "REJECTED")
        self.assertTrue(self.local.is_local)

    @expectedFailure
    def test_accepted_proposal_is_not_published_without_review(self):
        """Rapport 2.4 : une proposition acceptée devient globale et publiée sans relecture."""
        proposal = ActivityProposal.objects.create(activity=self.local, teacher=self.teacher)
        self.login(self.designer)
        self.client.post(reverse("handle_proposal", args=[proposal.id, "accept"]))
        self.local.refresh_from_db()
        self.assertFalse(self.local.is_local)
        self.assertNotEqual(self.local.status, "PUBLISHED")

