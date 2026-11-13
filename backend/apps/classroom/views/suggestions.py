from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_teacher
from apps.classroom.utils import compute_sequence_stats
from apps.learning.models import Result
from apps.pedagogy.models import Activity, Sequence, Session

from ..forms import (
    AddSequenceToClassForm,
    AddStudentForm,
    ClasseForm,
    JoinClassForm,
    LocalActivityForm,
    SuggestionForm,
)
from ..models import ActivitySelection, Classe, SessionCompletion, Suggestion
from ..utils import get_student_global_score


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

