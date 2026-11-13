from django import template

from apps.classroom.models import Suggestion

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Checks if the user belongs to a specific group.
    """
    return user.groups.filter(name=group_name).exists()


@register.simple_tag
def get_unread_suggestions_count(user):
    """
    Returns the number of unread suggestions for a given user.
    """
    if user.is_authenticated:
        return Suggestion.objects.filter(student=user, is_read=False).count()
    return 0