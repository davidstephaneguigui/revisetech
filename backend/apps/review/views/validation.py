from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer, is_referee
from apps.pedagogy.models import Sequence, Session

from ..forms import DevalidationForm


@require_POST
@login_required
@is_referee
def validate_sequence(request, sequence_id):
    """
    Allows a referee to validate a sequence and generates the session skeleton.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if request.user.groups.filter(name='Référent').exists():
        if sequence.status == 'PENDING':
            # Get the comment from the form
            comment = request.POST.get('referee_comment', '')
            if comment:
                sequence.referee_comment = comment
                
            sequence.status = 'VALIDATED'
            sequence.needs_second_review = False # Reset the flag
            sequence.save()
            
            # Generate or update real Sessions from PlannedSessions
            planned_sessions = sequence.planned_sessions.all().order_by('order')
            for planned in planned_sessions:
                Session.objects.update_or_create(
                    sequence=sequence,
                    order=planned.order,
                    defaults={
                        'name': planned.name,
                        'objective': planned.objective,
                        'session_type': planned.session_type,
                    }
                )
            
            messages.success(request, f"L'intention de la séquence '{sequence.name}' a été validée. Le squelette des séances a été généré.")
    
    return redirect(reverse('referee_dashboard') + '?section=intentions')


@require_POST
@login_required
@is_referee
def reject_sequence(request, sequence_id):
    """
    Allows a referee to reject a sequence with a mandatory reason and comment.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if sequence.status == 'PENDING':
        form = DevalidationForm(request.POST)
        if form.is_valid():
            # Save the review action for history
            action = form.save(commit=False)
            action.sequence = sequence
            action.user = request.user
            action.action_type = 'REJECT_INTENT'
            action.save()
            
            # Change status back to draft
            sequence.status = 'DRAFT'
            sequence.save()
            messages.warning(request, f"La séquence '{sequence.name}' a été rejetée.")
        else:
            messages.error(request, "Vous devez obligatoirement justifier votre rejet par un commentaire.")
    
    return redirect('referee_dashboard')


@require_POST
@login_required
@is_referee
def invalidate_sequence(request, sequence_id):
    """
    Allows a referee to cancel a validation with a mandatory reason and comment.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    # On vérifie d'abord si le statut permet l'annulation
    if sequence.status not in ['VALIDATED', 'CONTENT_PENDING', 'CONTENT_VALIDATED']:
        messages.error(request, "Cette action n'est pas autorisée pour cette séquence.")
        return redirect('referee_dashboard')

    form = DevalidationForm(request.POST)
    if form.is_valid():
        action = form.save(commit=False)
        action.sequence = sequence
        action.user = request.user
        
        # Case 1: Cancelling intention validation
        if sequence.status == 'VALIDATED':
            action.action_type = 'INVALIDATE_INTENT'
            sequence.status = 'DRAFT'
            
        # Case 2: Cancelling content validation
        elif sequence.status in ['CONTENT_PENDING', 'CONTENT_VALIDATED']:
            action.action_type = 'INVALIDATE_CONTENT'
            sequence.status = 'VALIDATED'
            
        action.save()
        sequence.save()
        messages.warning(request, f"La validation de la séquence '{sequence.name}' a été annulée.")
    else:
        messages.error(request, "Vous devez obligatoirement justifier cette annulation par un commentaire.")
            
    return redirect('referee_dashboard')


@require_POST
@login_required
@is_referee
def validate_content(request, sequence_id):
    """
    Allows a referee to validate the final content of a sequence with a comment.
    Handles both first validation and second reviews.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    comment = request.POST.get('referee_comment', '')
    
    # Case 1: First validation of the content
    if sequence.status == 'CONTENT_PENDING':
        sequence.status = 'CONTENT_VALIDATED'
        sequence.referee_comment = comment
        sequence.first_referee = request.user  # <-- On enregistre l'auteur du premier avis
        sequence.save()
        
        messages.success(request, f"Le contenu de la séquence '{sequence.name}' a été validé.")
        
        chapter = sequence.chapter
        all_validated = chapter.sequences.filter(status='CONTENT_VALIDATED').count() == chapter.sequences.count()
        
        if all_validated:
            chapter.status = 'PENDING_PUBLISHING'
            chapter.save()
            messages.success(request, f"Le chapitre '{chapter.name}' est complet et prêt pour la publication.")
            
    # Case 2: Second review requested by the supervisor
    elif sequence.status == 'CONTENT_VALIDATED' and sequence.needs_second_review:
        # <-- NOUVEAU : On vérifie que ce n'est pas le même référent
        if sequence.first_referee == request.user:
            messages.error(request, "Vous ne pouvez pas donner un second avis sur une séquence que vous avez déjà validée. Un autre référent doit intervenir.")
            return redirect('referee_dashboard')
            
        sequence.referee_comment += f"\n\n--- Second avis ---\n{comment}"
        sequence.needs_second_review = False
        sequence.save()
        messages.success(request, f"Votre second avis sur la séquence '{sequence.name}' a été enregistré.")
            
    return redirect(reverse('referee_dashboard') + '?section=contents')


@require_POST
@login_required
@is_designer
def submit_content(request, sequence_id):
    """
    Allows the designer to submit the filled sequence content to the referee.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    
    if sequence.status == 'VALIDATED':
        sequence.status = 'CONTENT_PENDING'
        sequence.save()
        messages.success(request, "Le contenu de la séquence a été soumis au référent pour validation.")
    
    return redirect('manage_sequence', sequence_id=sequence.id)

