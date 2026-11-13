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
def student_profile(request, student_id):
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    # Sécurité : Vérifier que l'élève est bien dans une classe de l'enseignant
    teacher_classes = Classe.objects.filter(main_teacher=request.user, students=student)
    if not teacher_classes.exists():
        return HttpResponseForbidden("Vous n'avez pas accès à cet élève.")
    
    classe = teacher_classes.first() # Pour le fil d'Ariane

    # 1. Historique complet des résultats
    results = Result.objects.filter(student=student).order_by('-id')

    # 2. Répartition par matière
    subjects_stats = {}
    for res in results:
        if not res.activity: continue
        try:
            # On remonte la chaîne pour trouver la matière
            matiere_name = res.activity.sessions.first().sequence.chapter.matiere.name
            if matiere_name not in subjects_stats:
                subjects_stats[matiere_name] = {'obtained': 0, 'total': 0}
            subjects_stats[matiere_name]['obtained'] += res.score
            subjects_stats[matiere_name]['total'] += res.activity.questions.count()
        except Exception:
            pass # Ignore si la chaîne de relation est incomplète
            
    subjects_breakdown = []
    for name, stats in subjects_stats.items():
        if stats['total'] > 0:
            avg = (stats['obtained'] / stats['total']) * 20
            subjects_breakdown.append({'name': name, 'average': round(avg, 1)})

    # 3. Les suggestions
    suggestions = Suggestion.objects.filter(student=student).order_by('-id')
    
    # Fil d'Ariane
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Élèves', 'url': reverse('teacher_results')},
        {'label': classe.name, 'url': reverse('class_results', args=[classe.id])},
        {'label': student.username, 'url': None}
    ]

    context = {
        'student': student,
        'results': results,
        'subjects_breakdown': subjects_breakdown,
        'suggestions': suggestions,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/student_profile.html', context)


@login_required
def student_results(request, student_id):
    """
    Display the results of a specific student and handle sending suggestions.
    """
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    is_my_student = Classe.objects.filter(main_teacher=request.user, students=student).exists()
    if not is_my_student:
        messages.error(request, "Vous n'avez pas accès aux résultats de cet élève.")
        return redirect('teacher_dashboard')

    results = Result.objects.filter(student=student).order_by('-date_attempt')
    
    if request.method == 'POST':
        form = SuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.teacher = request.user
            suggestion.student = student
            suggestion.save()
            messages.success(request, f"La suggestion a bien été envoyée à {student.username}.")
            return redirect('student_results', student_id=student.id)
    else:
        form = SuggestionForm()
    
    context = {
        'student': student,
        'results': results,
        'form': form
    }
    
    return render(request, 'classroom/student_results.html', context)

