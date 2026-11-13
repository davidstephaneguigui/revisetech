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
def create_local_activity(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    session = get_object_or_404(Session, id=session_id)
    
    if request.method == 'POST':
        form = LocalActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.is_local = True
            activity.creator = request.user
            activity.classe = classe
            activity.status = 'PUBLISHED'
            
            # 1. On sauvegarde d'abord l'activité en base de données
            activity.save() 
            
            # 2. On ajoute la séance à la relation ManyToMany
            activity.sessions.add(session)
            
            messages.success(request, "L'activité locale a été ajoutée à cette séance.")
            return redirect('prepare_session', class_id=classe.id, session_id=session.id)
    else:
        form = LocalActivityForm()

    return render(request, 'classroom/create_local_activity.html', {
        'form': form,
        'classe': classe,
        'session': session
    })


@require_POST
@login_required
@is_teacher
def import_global_activity(request, activity_id):
    global_activity = get_object_or_404(Activity, id=activity_id, is_local=False)
    
    # On récupère la séance d'origine pour la redirection
    session = global_activity.sessions.first()
    
    # On crée la copie locale
    local_activity = Activity.objects.create(
        title=f"{global_activity.title} (Copie)",
        content=global_activity.content,
        activity_type=global_activity.activity_type,
        is_local=True,
        creator=request.user,
        status='PUBLISHED'
    )
    
    # On la lie à la séance d'origine pour qu'elle apparaisse dans la préparation
    if session:
        local_activity.sessions.add(session)
        
    # On demande à l'enseignant de choisir sa classe (pour l'instant, on prend la première)
    # Idéalement, il faudrait un select, mais en TGV on fait au plus simple pour tester
    classe = request.user.main_classes.first()
    if classe:
        local_activity.classe = classe
        local_activity.save()
        
        messages.success(request, f"L'activité a été ajoutée à votre classe {classe.name}.")
        return redirect('prepare_session', class_id=classe.id, session_id=session.id)
    
    messages.error(request, "Vous n'avez pas de classe pour ajouter cette activité.")
    return redirect('activity_bank')


@require_POST
@login_required
@is_teacher
def toggle_activity_usage(request, class_id, activity_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    
    selection, created = ActivitySelection.objects.get_or_create(
        classe=classe, 
        activity_id=activity_id
    )
    
    selection.is_used = not selection.is_used
    selection.save()
    
    return JsonResponse({'status': 'success', 'is_used': selection.is_used})


@require_POST
@login_required
@is_teacher
def move_activity(request, class_id, session_id, activity_id, direction):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    session = get_object_or_404(Session, id=session_id)
    
    activities = session.activities.all()
    
    for act in activities:
        ActivitySelection.objects.get_or_create(classe=classe, activity=act)
        
    selections = list(ActivitySelection.objects.filter(classe=classe, activity__in=activities).order_by('order', 'id'))
    
    for i, sel in enumerate(selections):
        if sel.order != i:
            sel.order = i
            sel.save()
            
    current_idx = next((i for i, s in enumerate(selections) if s.activity_id == int(activity_id)), None)
    
    if current_idx is not None:
        if direction == 'up' and current_idx > 0:
            swap_idx = current_idx - 1
        elif direction == 'down' and current_idx < len(selections) - 1:
            swap_idx = current_idx + 1
        else:
            return redirect('prepare_session', class_id=classe.id, session_id=session.id)
            
        selections[current_idx].order, selections[swap_idx].order = selections[swap_idx].order, selections[current_idx].order
        selections[current_idx].save()
        selections[swap_idx].save()
        
    return redirect('prepare_session', class_id=classe.id, session_id=session.id)


@require_POST
@login_required
@is_teacher
def add_existing_activity(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    session = get_object_or_404(Session, id=session_id)
    
    activity_id = request.POST.get('global_activity_id')
    if not activity_id:
        messages.error(request, "Veuillez sélectionner une activité.")
        return redirect('prepare_session', class_id=classe.id, session_id=session.id)

    original_activity = get_object_or_404(Activity, id=activity_id, is_local=False)
    
    # On clone l'activité pour en faire une activité locale à la classe
    new_activity = Activity.objects.create(
        title=f"{original_activity.title} (Copie)",
        content=original_activity.content,
        activity_type=original_activity.activity_type,
        is_local=True,
        creator=request.user,
        classe=classe,
        status='PUBLISHED'
    )
    # On l'attache à la séance
    new_activity.sessions.add(session)
    
    messages.success(request, f"L'activité '{original_activity.title}' a été ajoutée à votre séance.")
    return redirect('prepare_session', class_id=classe.id, session_id=session.id)

