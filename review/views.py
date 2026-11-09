from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from pedagogy.models import Sequence, Session
from django.db.models import Q
from accounts.decorators import role_required
from accounts.decorators import is_designer, is_referee, is_inspector


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
            chapter.status = 'PENDING_INSPECTION'
            chapter.save()
            messages.success(request, f"Le chapitre '{chapter.name}' est complet et prêt pour l'inspection.")
            
    # Case 2: Second review requested by the Inspector
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
    Display the dashboard for referees, showing pending intentions, 
    pending contents, validated sequences, and content validated.
    """
    # 1. Intentions waiting for validation
    pending_sequences = Sequence.objects.filter(status='PENDING').order_by('chapter__matiere__name', 'name')
      
    # 2. Sequences validated (currently filling content)
    validated_sequences = Sequence.objects.filter(status='VALIDATED').order_by('-id')

    # 3. Sequences waiting for content validation
    content_pending_sequences = Sequence.objects.filter(status='CONTENT_PENDING').order_by('chapter__matiere__name', 'name')

    # 4. Content validated (waiting for publication)
    content_validated_sequences = Sequence.objects.filter(status='CONTENT_VALIDATED').order_by('-id')

    # 5. Content which need a second validation
    second_review_sequences = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=True).order_by('-id')

    # 6. Sequences published
    published_sequences = Sequence.objects.filter(status='PUBLISHED').order_by('chapter__matiere__name', 'chapter__name', 'name')

    # Prepare sessions with is_new flag for the template
    for seq in validated_sequences:
        planned_orders = set(seq.planned_sessions.values_list('order', flat=True))
        sessions_with_flags = list(seq.sessions.all())
        for sess in sessions_with_flags:
            sess.is_new = sess.order not in planned_orders
        seq.sessions_with_flags = sessions_with_flags
    
    context = {
        'pending_sequences': pending_sequences,
        'content_pending_sequences': content_pending_sequences,
        'validated_sequences': validated_sequences,
        'content_validated_sequences': content_validated_sequences,
        'second_review_sequences': second_review_sequences,
        'published_sequences': published_sequences,
    }
    
    return render(request, 'review/referee_home.html', context)


@login_required
@is_inspector
def inspector_dashboard(request):
    """
    Display the dashboard for inspectors.
    Shows sequences in preparation, ready to be published, and already published.
    """
    # Sequences in preparation (intention validated, content being filled)
    sequences_in_preparation = Sequence.objects.filter(status='VALIDATED').order_by('chapter__matiere__name', 'chapter__name', 'name')
    
    # Sequences ready for publication
    sequences_to_publish = Sequence.objects.filter(status='CONTENT_VALIDATED').order_by('chapter__matiere__name', 'chapter__name', 'name')
    
    # Published sequences
    published_sequences = Sequence.objects.filter(status='PUBLISHED').order_by('chapter__matiere__name', 'chapter__name', 'name')
    
    context = {
        'sequences_in_preparation': sequences_in_preparation,
        'sequences_to_publish': sequences_to_publish,
        'published_sequences': published_sequences,
    }
    
    return render(request, 'review/inspector_home.html', context)


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
    Allows a referee to reject a sequence, sending it back to draft.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    if request.user.groups.filter(name='Référent').exists():
        sequence.status = 'DRAFT'
        sequence.save()
        messages.warning(request, f"La séquence '{sequence.name}' a été rejetée et repassée en brouillon.")
    return redirect('referee_dashboard')


@require_POST
@login_required
@is_referee
def invalidate_sequence(request, sequence_id):
    """
    Allows a referee to cancel a validation.
    - If intention was validated: sends back to DRAFT.
    - If content was submitted/validated: sends back to VALIDATED (intention remains good).
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if request.user.groups.filter(name='Référent').exists():
        
        # Case 1: Annulation de la validation de l'intention
        if sequence.status == 'VALIDATED':
            sequence.status = 'DRAFT'
            sequence.save()
            messages.warning(request, f"La validation de l'intention de la séquence '{sequence.name}' a été annulée. Elle est repassée en brouillon.")
            
        # Case 2: Annulation de la validation du contenu
        elif sequence.status in ['CONTENT_PENDING', 'CONTENT_VALIDATED']:
            sequence.status = 'VALIDATED'
            sequence.save()
            messages.warning(request, f"La validation du contenu de la séquence '{sequence.name}' a été annulée. Le concepteur peut maintenant le modifier.")
            
        # If the chapter was pending inspection, send it back to draft
        chapter = sequence.chapter
        if chapter.status == 'PENDING':
            chapter.status = 'DRAFT'
            chapter.save()
                
    return redirect('referee_dashboard')


@require_POST
@login_required
@is_inspector
def publish_sequence(request, sequence_id):
    """
    Allows an inspector to publish a specific sequence. 
    If all sequences in the chapter are published, the chapter is published too.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if sequence.status == 'CONTENT_VALIDATED':
        # 1. Publish the sequence itself
        sequence.status = 'PUBLISHED'
        sequence.save()
        
        # 2. Publish all sessions and activities inside this sequence
        for session in sequence.sessions.all():
            session.status = 'PUBLISHED'
            session.save()
            for activity in session.activities.all():
                activity.status = 'PUBLISHED'
                activity.save()
        
        # 3. Check if all sequences in the chapter are now published
        chapter = sequence.chapter
        all_published = chapter.sequences.exclude(status='PUBLISHED').count() == 0
        
        if all_published:
            chapter.status = 'PUBLISHED'
            chapter.save()
            messages.success(request, f"La séquence '{sequence.name}' a été publiée. Toutes les séquences du chapitre étant publiées, le chapitre '{chapter.name}' est désormais publié.")
        else:
            messages.success(request, f"La séquence '{sequence.name}' a été publiée. Le chapitre est en attente de publication des autres séquences.")
            
    return redirect('inspector_dashboard')


@require_POST
@login_required
@is_inspector
def request_second_review(request, sequence_id):
    """
    Allows an inspector to request a second review from another referee.
    The status remains CONTENT_VALIDATED but the flag is raised.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if sequence.status == 'CONTENT_VALIDATED':
        sequence.needs_second_review = True
        sequence.save()
        messages.success(request, f"Une seconde validation a été demandée pour la séquence '{sequence.name}'.")
            
    return redirect('inspector_dashboard')