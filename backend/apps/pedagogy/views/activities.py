from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from apps.accounts.decorators import get_user_roles
from apps.classroom.models import Suggestion


def can_view_unpublished(user):
    """
    Returns True if the user is allowed to see unpublished content.
    Students (and anonymous users) are not allowed.
    """
    if not user.is_authenticated:
        return False
    # Staff and superusers can always see unpublished content
    if user.is_staff or user.is_superuser:
        return True
    
    # Teachers, designers, referees, supervisors can see unpublished content
    user_roles = get_user_roles(user)
    privileged_roles = {'Enseignant', 'Concepteur', 'Référent', 'Superviseur', 'Administrateur'}
    return bool(user_roles & privileged_roles)


@login_required
def mark_suggestion_read(request, suggestion_id):
    """
    Marks a suggestion as read and redirects the student to the activity.
    """
    suggestion = get_object_or_404(Suggestion, id=suggestion_id, student=request.user)
    suggestion.is_read = True
    suggestion.save()
    return redirect('activity_detail', activity_id=suggestion.activity.id)