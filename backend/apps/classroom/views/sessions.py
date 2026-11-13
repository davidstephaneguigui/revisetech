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
def prepare_session(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    session = get_object_or_404(Session, id=session_id)
    
    # On crée les sélections manquantes sans casser l'ordre existant
    for act in session.activities.all():
        ActivitySelection.objects.get_or_create(classe=classe, activity=act)

    # On récupère les sélections triées
    selections = ActivitySelection.objects.filter(
        classe=classe, 
        activity__in=session.activities.all()
    ).order_by('order', 'id')
    
    # 1. On s'assure que toutes les activités ont une sélection
    for act in session.activities.all():
        ActivitySelection.objects.get_or_create(classe=classe, activity=act)

    # 2. On récupère toutes les sélections triées par ordre
    selections = ActivitySelection.objects.filter(
        classe=classe, 
        activity__in=session.activities.all()
    ).order_by('order', 'id')
    
    # 3. On crée une seule liste d'activités fusionnées
    all_activities = [s.activity for s in selections]
    
    # (On garde all_global_activities pour la modale d'ajout)
    all_global_activities = Activity.objects.filter(is_local=False).order_by('title')

    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Classes', 'url': reverse('teacher_results')},
        {'label': classe.name, 'url': reverse('class_detail', args=[classe.id])},
        {'label': session.sequence.name, 'url': reverse('class_sequence_detail', args=[classe.id, session.sequence.id])},
        {'label': session.name, 'url': None}
    ]
    context = {
        'classe': classe,
        'session': session,
        'all_activities': all_activities, # <-- La nouvelle liste fusionnée
        'all_global_activities': all_global_activities,
        'breadcrumbs': breadcrumbs,
        'selected_activity_ids': list(classe.selected_activities.filter(is_used=True).values_list('activity_id', flat=True)),
    }
    return render(request, 'classroom/prepare_session.html', context)


@require_POST
@login_required
@is_teacher
def toggle_session_completion(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    
    # On cherche ou on crée l'enregistrement
    completion, created = SessionCompletion.objects.get_or_create(
        classe=classe, 
        session_id=session_id
    )
    
    # On inverse l'état
    completion.is_completed = not completion.is_completed
    completion.save()
    
    # On renvoie une réponse JSON pour que le JS puisse mettre à jour l'icône sans recharger la page
    return JsonResponse({
        'status': 'success', 
        'is_completed': completion.is_completed
    })


@require_POST
@login_required
@is_teacher
def move_session(request, class_id, sequence_id, session_id, direction):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    # 1. On récupère toutes les séances
    sessions = sequence.sessions.all()
    
    # 2. On s'assure que tout est créé
    for sess in sessions:
        SessionCompletion.objects.get_or_create(classe=classe, session=sess)
        
    # 3. On réinitialise les ordres pour qu'ils soient uniques (0, 1, 2, 3...)
    completions = list(SessionCompletion.objects.filter(classe=classe, session__in=sessions).order_by('order', 'id'))
    
    for i, comp in enumerate(completions):
        if comp.order != i:
            comp.order = i
            comp.save()
            
    # 4. On trouve l'index et on échange
    current_idx = next((i for i, c in enumerate(completions) if c.session_id == int(session_id)), None)
    
    if current_idx is not None:
        if direction == 'up' and current_idx > 0:
            swap_idx = current_idx - 1
        elif direction == 'down' and current_idx < len(completions) - 1:
            swap_idx = current_idx + 1
        else:
            return redirect('class_sequence_detail', class_id=classe.id, sequence_id=sequence.id)
            
        completions[current_idx].order, completions[swap_idx].order = completions[swap_idx].order, completions[current_idx].order
        completions[current_idx].save()
        completions[swap_idx].save()
        
    return redirect('class_sequence_detail', class_id=classe.id, sequence_id=sequence.id)

