from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from apps.regulation.models import ReviewAction

# Dictionnaire des transitions autorisées
# Format : "action": (statuts_de_depart, statut_d_arrivee, role_requis)
TRANSITIONS = {
    "submit_intention": ({"DRAFT"}, "PENDING", "Concepteur"),
    "validate_intention": ({"PENDING"}, "VALIDATED", "Régulateur"),
    "submit_content": ({"VALIDATED"}, "CONTENT_PENDING", "Concepteur"),
    "validate_content": ({"CONTENT_PENDING"}, "CONTENT_VALIDATED", "Régulateur"),
    "publish": ({"CONTENT_VALIDATED"}, "PUBLISHED", "Régulateur"),
    "unpublish": ({"PUBLISHED"}, "CONTENT_VALIDATED", "Régulateur"),
}

def apply(sequence, action, user, comment=""):
    """
    Applique une transition de statut à une séquence.
    Vérifie les droits, le statut actuel, et met à jour la cascade (séances/activités).
    Enregistre également l'action dans l'historique (ReviewAction).
    """
    if action not in TRANSITIONS:
        raise ValueError(f"Action inconnue : {action}")

    sources, target, required_role = TRANSITIONS[action]

    # 1. Vérification du rôle
    user_groups = list(user.groups.values_list('name', flat=True))
    
    # On accepte les anciens noms de rôles pour assurer la transition
    required_roles = [required_role]
    if required_role == "Régulateur":
        required_roles.extend(["Référent", "Superviseur"])

    if not any(role in user_groups for role in required_roles):
        raise PermissionDenied(_("Vous n'avez pas le rôle requis pour cette action."))

    # 2. Vérification du statut actuel
    if sequence.status not in sources:
        raise ValueError(_(f"Transition impossible depuis le statut {sequence.status}."))

    # 3. Mise à jour du statut de la séquence
    sequence.status = target
    if comment and action in ["validate_intention", "validate_content"]:
        sequence.referee_comment = comment
    sequence.save()

    # 4. Cascade sur les séances et activités
    if action == "publish":
        for session in sequence.sessions.all():
            session.status = 'PUBLISHED'
            session.save()
            for activity in session.activities.all():
                activity.status = 'PUBLISHED'
                activity.save()
                
    elif action == "unpublish":
        for session in sequence.sessions.all():
            session.status = 'DRAFT'
            session.save()
            for activity in session.activities.all():
                if not activity.is_local:
                    activity.status = 'DRAFT'
                    activity.save()

    # 5. Enregistrement de l'historique
    ReviewAction.objects.create(
        sequence=sequence, 
        user=user, 
        action_type=action, 
        comment=comment
    )

    return sequence