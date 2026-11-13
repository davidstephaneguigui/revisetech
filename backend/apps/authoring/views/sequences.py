from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer, is_teacher
from apps.pedagogy.models import (
    Activity,
    Chapter,
    Choice,
    PlannedSession,
    Question,
    Sequence,
    Session,
)

from ..forms import (
    ActivityForm,
    ChoiceForm,
    PlannedSessionForm,
    QuestionForm,
    SequenceForm,
    SequenceIntentionForm,
    SessionForm,
)
from ..models import ActivityProposal


@login_required
@is_designer
def designer_chapter_detail(request, chapter_id):
    """Niveau 2 : Liste des séquences d'un chapitre spécifique."""
    chapter = get_object_or_404(Chapter, id=chapter_id)
    sequences = Sequence.objects.filter(chapter=chapter, creator=request.user).order_by('name')
    
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mon Atelier', 'url': reverse('designer_dashboard')},
        {'label': chapter.name, 'url': None}
    ]
    
    context = {
        'chapter': chapter,
        'sequences': sequences,
        'breadcrumbs': breadcrumbs,
        'pending_proposals_count': ActivityProposal.objects.filter(status='PENDING').count(),
    }
    return render(request, 'authoring/designer_chapter_detail.html', context)


@login_required
@is_designer
def create_sequence(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        chapter_id = request.POST.get('chapter')
        
        if name and chapter_id:
            try:
                chapter = Chapter.objects.get(id=chapter_id)
                Sequence.objects.create(
                    name=name,
                    chapter=chapter,
                    creator=request.user,
                    status='DRAFT'  # Assure-toi que le statut par défaut est bien DRAFT
                )
                messages.success(request, "Séquence créée avec succès.")
            except Chapter.DoesNotExist:
                messages.error(request, "Chapitre introuvable.")
        else:
            messages.error(request, "Erreur : tous les champs sont requis.")
            
        return redirect('designer_dashboard')
    return redirect('designer_dashboard')


@login_required
@is_designer
def manage_sequence(request, sequence_id):
    """
    Display the sequence details and handle intention submission or session creation.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    sessions = sequence.sessions.all()
    
    PlannedSessionFormSet = inlineformset_factory(
        Sequence, 
        PlannedSession, 
        form=PlannedSessionForm, 
        extra=1, 
        can_delete=True
    )
    
    intention_form = SequenceIntentionForm(instance=sequence)
    planned_sessions_formset = PlannedSessionFormSet(instance=sequence)
    session_form = SessionForm()
    
    if request.method == 'POST':
        # 1. Handle intention submission
        if 'save_intention' in request.POST or 'submit_intention' in request.POST:
            intention_form = SequenceIntentionForm(request.POST, instance=sequence)
            planned_sessions_formset = PlannedSessionFormSet(request.POST, instance=sequence)
            
            if intention_form.is_valid() and planned_sessions_formset.is_valid():
                seq = intention_form.save(commit=False)
                if 'submit_intention' in request.POST:
                    seq.status = 'PENDING'
                    messages.success(request, "La séquence a été soumise pour validation.")
                else:
                    messages.success(request, "Les caractéristiques ont été enregistrées.")
                seq.save()
                planned_sessions_formset.save()
                return redirect('manage_sequence', sequence_id=sequence.id)
                
        # 2. Handle adding a new session after intention validation
        elif 'add_session' in request.POST:
            session_form = SessionForm(request.POST)
            if session_form.is_valid():
                session = session_form.save(commit=False)
                session.sequence = sequence
                
                # Auto-increment the order
                last_session = sequence.sessions.order_by('-order').first()
                session.order = (last_session.order + 1) if last_session else 1
                session.save()
                
                # Flag the sequence as having changes that need review, without blocking the designer
                sequence.has_unreviewed_changes = True
                sequence.save()

                
                
                messages.warning(request, "La séance a été ajoutée. Le référent sera notifié de cette modification lors de sa prochaine lecture.")
                return redirect('manage_sequence', sequence_id=sequence.id)

    review_actions = sequence.review_actions.all()    
    
    context = {
        'sequence': sequence,
        'sessions': sessions,
        'intention_form': intention_form,
        'planned_sessions_formset': planned_sessions_formset,
        'session_form': session_form,
        'review_actions' : review_actions,
    }
    
    return render(request, 'authoring/manage_sequence.html', context)


@require_POST
@login_required
@is_designer
def delete_sequence(request, sequence_id):
    """
    Allows the designer to delete a sequence ONLY if it is in DRAFT status.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    
    if sequence.status == 'DRAFT':
        sequence.delete()
        messages.success(request, "La séquence a été supprimée définitivement.")
        return redirect('designer_dashboard')
    else:
        messages.error(request, "Vous ne pouvez pas supprimer une séquence qui est déjà engagée dans le processus de validation.")
        return redirect('manage_sequence', sequence_id=sequence.id)

