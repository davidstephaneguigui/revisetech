from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from pedagogy.models import Sequence, Session
from django.db.models import Q
from accounts.decorators import is_designer, is_referee
from .forms import DevalidationForm


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
        sequence.referee_comment += f"\n\n--- Second avis ---\n{comment}"
        sequence.needs_second_review = False
        sequence.save()
        messages.success(request, f"Votre second avis sur la séquence '{sequence.name}' a été enregistré.")
            
    return redirect('referee_dashboard')


@login_required
@is_referee
def referee_dashboard(request):
    """
    Display the dashboard for referees.
    """
    # 1. Sequences waiting for intention validation
    pending_sequences = Sequence.objects.filter(status='PENDING').order_by('chapter__matiere__name', 'name')
    
    # 2. Sequences waiting for content validation
    content_pending_sequences = Sequence.objects.filter(status='CONTENT_PENDING').order_by('chapter__matiere__name', 'name')
    
    # 3. Sequences validated (currently filling content)
    validated_sequences = Sequence.objects.filter(status='VALIDATED').order_by('-id')

    # 4. Content validated (waiting for publication)
    content_validated_sequences = Sequence.objects.filter(status='CONTENT_VALIDATED').order_by('-id')

    # 5. Content which need a second validation
    second_review_sequences = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=True).order_by('-id')

    # 6. Sequences published
    published_sequences = Sequence.objects.filter(status='PUBLISHED').order_by('chapter__matiere__name', 'chapter__name', 'name')

    # Instanciation of unvalidate form
    deval_form = DevalidationForm()
    
    context = {
        'pending_sequences': pending_sequences,
        'content_pending_sequences': content_pending_sequences,
        'validated_sequences': validated_sequences,
        'content_validated_sequences': content_validated_sequences,
        'second_review_sequences': second_review_sequences,
        'published_sequences': published_sequences,
        'deval_form': deval_form,
        'open_section': request.GET.get('section', ''),
    }
    
    return render(request, 'review/referee_home.html', context)


@login_required
@is_referee
def compare_sequences(request, sequence_id_1):
    """
    Allows a referee to compare two sequences side-by-side, with search functionality.
    """
    sequence1 = get_object_or_404(Sequence, id=sequence_id_1)
    
    query = request.GET.get('q', '')
    
    # Base queryset: all sequences except the first one
    other_sequences = Sequence.objects.exclude(id=sequence_id_1)
    
    if query:
        # Search by sequence name, tags, chapter name, or subject name
        other_sequences = other_sequences.filter(
            Q(name__icontains=query) | 
            Q(tags__icontains=query) |
            Q(chapter__name__icontains=query) |
            Q(chapter__matiere__name__icontains=query)
        )
        
    other_sequences = other_sequences.order_by('chapter__matiere__name', 'name')
    
    sequence2 = None
    sequence_id_2 = request.GET.get('compare_with')
    if sequence_id_2:
        sequence2 = get_object_or_404(Sequence, id=sequence_id_2)
        
    context = {
        'sequence1': sequence1,
        'sequence2': sequence2,
        'other_sequences': other_sequences,
        'query': query,
        'sequence_id_2': sequence_id_2
    }
    
    return render(request, 'review/compare_sequences.html', context)


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
    
    return redirect('referee_dashboard')


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