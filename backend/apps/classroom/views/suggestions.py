from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ..models import Suggestion


@login_required
def suggestion_list(request):
    """
    Display all suggestions received by the student.
    """
    # Fetch all suggestions for the student, most recent first
    suggestions = Suggestion.objects.filter(student=request.user).order_by('-created_at')
    
    # Mark all as read when the student opens the list
    unread_suggestions = suggestions.filter(is_read=False)
    unread_suggestions.update(is_read=True)
    
    context = {
        'suggestions': suggestions
    }
    
    return render(request, 'classroom/suggestion_list.html', context)

