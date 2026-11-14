"""Rôles : hiérarchie et contrôle d'accès aux espaces réservés."""

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.accounts.decorators import get_user_roles
from apps.testing import ADMIN, RevisetechTestCase, make_user

# Tableau de bord de chaque espace, et rôle minimum pour y entrer
SPACES = {
    "teacher_dashboard": "teacher",
    "designer_dashboard": "designer",
    "referee_dashboard": "referee",
    "supervisor_dashboard": "supervisor",
}


class RoleHierarchyTests(RevisetechTestCase):
    def test_anonymous_user_has_no_role(self):
        self.assertEqual(get_user_roles(AnonymousUser()), set())

    def test_student_has_no_role(self):
        self.assertEqual(get_user_roles(self.student), set())

    def test_teacher_has_only_teacher_role(self):
        self.assertEqual(get_user_roles(self.teacher), {"Enseignant"})

    def test_referee_inherits_designer_and_teacher(self):
        self.assertEqual(
            get_user_roles(self.referee), {"Référent", "Concepteur", "Enseignant"}
        )

    def test_supervisor_inherits_all_lower_roles(self):
        self.assertEqual(
            get_user_roles(self.supervisor),
            {"Superviseur", "Référent", "Concepteur", "Enseignant"},
        )

    def test_administrator_group_has_every_role(self):
        admin = make_user("admin", ADMIN)
        self.assertIn("Superviseur", get_user_roles(admin))
        self.assertIn("Administrateur", get_user_roles(admin))

    def test_superuser_has_every_role(self):
        root = make_user("root")
        root.is_superuser = True
        root.save()
        self.assertIn("Superviseur", get_user_roles(root))


class SpaceAccessTests(RevisetechTestCase):
    def test_anonymous_is_sent_to_login(self):
        for url_name in SPACES:
            with self.subTest(space=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_student_gets_403_on_every_reserved_space(self):
        self.login(self.student)
        for url_name in SPACES:
            with self.subTest(space=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 403)

    def test_each_role_opens_its_own_space(self):
        for url_name, attribute in SPACES.items():
            with self.subTest(space=url_name):
                self.login(getattr(self, attribute))
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_teacher_cannot_open_higher_spaces(self):
        self.login(self.teacher)
        for url_name in ("designer_dashboard", "referee_dashboard", "supervisor_dashboard"):
            with self.subTest(space=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 403)

    def test_designer_cannot_open_review_or_publishing(self):
        self.login(self.designer)
        for url_name in ("referee_dashboard", "supervisor_dashboard"):
            with self.subTest(space=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 403)

    def test_supervisor_opens_lower_spaces_by_inheritance(self):
        self.login(self.supervisor)
        for url_name in SPACES:
            with self.subTest(space=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

# Create your tests here.
