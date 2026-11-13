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
@is_teacher
def teacher_dashboard(request):
    """
    Display the dashboard for teachers and handle class creation.
    """
    classes = Classe.objects.filter(main_teacher=request.user)
    form = ClasseForm()
    
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            classe = form.save(commit=False)
            classe.main_teacher = request.user
            classe.save()
            return redirect('teacher_dashboard')
    
    context = {
        'classes': classes,
        'form': form
    }
    
    return render(request, 'classroom/teacher_home.html', context)


@login_required
@is_teacher
def teacher_preparations(request):
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes préparations', 'url': None}
    ]
    
    context = {
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/teacher_preparations.html', context)