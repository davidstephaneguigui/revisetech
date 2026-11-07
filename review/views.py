from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pedagogy.models import Sequence, Session, Chapter
from django.db.models import Q


@login_required
def submit_sequence(request, sequence_id):
    """
    Allows the designer to submit a sequence for validation.
    """
    # Remplace l'ancienne ligne par celle-ci :
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    
    if sequence.status == 'VALIDATED':
        sequence.status = 'CONTENT_PENDING'
        sequence.save()
        messages.success(request, "La séquence a été soumise au référent pour validation.")
    
    return redirect('manage_sequence', sequence_id=sequence.id)


@login_required
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


@login_required
def validate_content(request, sequence_id):
    """
    Allows a referee to validate the final content of a sequence with a comment.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if request.user.groups.filter(name='Référent').exists():
        if sequence.status == 'CONTENT_PENDING':
            # Get the comment from the form
            comment = request.POST.get('referee_comment', '')
            
            sequence.status = 'CONTENT_VALIDATED'
            sequence.referee_comment = comment
            sequence.save()
            
            messages.success(request, f"Le contenu de la séquence '{sequence.name}' a été validé.")
            
            # Check if all sequences in the chapter are now content-validated
            chapter = sequence.chapter
            all_validated = True
            for seq in chapter.sequences.all():
                if seq.status != 'CONTENT_VALIDATED':
                    all_validated = False
                    break
            
            if all_validated:
                chapter.status = 'PENDING' # PENDING_INSPECTION
                chapter.save()
                messages.success(request, f"Le chapitre '{chapter.name}' est complet et prêt pour l'inspection.")
                
    return redirect('referee_dashboard')


@login_required
def referee_dashboard(request):
    """
    Display the dashboard for referees, showing pending intentions, 
    pending content, and validated sequences.
    """
    pending_sequences = Sequence.objects.filter(status='PENDING').order_by('chapter__matiere__name', 'name')
    content_pending_sequences = Sequence.objects.filter(status='CONTENT_PENDING').order_by('chapter__matiere__name', 'name')
    validated_sequences = Sequence.objects.filter(status='VALIDATED').order_by('-id')
    content_validated_sequences = Sequence.objects.filter(status='CONTENT_VALIDATED').order_by('-id')
    
    context = {
        'pending_sequences': pending_sequences,
        'content_pending_sequences': content_pending_sequences,
        'validated_sequences': validated_sequences,
        'content_validated_sequences': content_validated_sequences,
    }
    
    return render(request, 'review/referee_home.html', context)


@login_required
def inspector_dashboard(request):
    """
    Display the dashboard for inspectors, showing sequences ready to be published.
    """
    # Fetch sequences that are validated by the referee and ready for publication
    sequences_to_publish = Sequence.objects.filter(status='CONTENT_VALIDATED').order_by('chapter__matiere__name', 'chapter__name', 'name')
    
    context = {
        'sequences_to_publish': sequences_to_publish
    }
    
    return render(request, 'review/inspector_home.html', context)


@login_required
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


@login_required
def validate_sequence(request, sequence_id):
    """
    Allows a referee to validate a sequence and generates the session skeleton.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if request.user.groups.filter(name='Référent').exists():
        if sequence.status == 'PENDING':
            sequence.status = 'VALIDATED'
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
                        # On ne met pas 'status' dans defaults pour ne pas écraser le travail déjà fait
                    }
                )
            
            # Check if all sequences in the chapter are now validated
            chapter = sequence.chapter
            all_validated = True
            for seq in chapter.sequences.all():
                if seq.status != 'VALIDATED':
                    all_validated = False
                    break
            
            if all_validated:
                chapter.status = 'PENDING' # PENDING_INSPECTION
                chapter.save()
                messages.success(request, f"Le chapitre '{chapter.name}' est maintenant complet et prêt pour l'inspection.")
            
            messages.success(request, f"L'intention de la séquence '{sequence.name}' a été validée. Le squelette des séances a été généré.")
    
    return redirect('referee_dashboard')


@login_required
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


@login_required
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


@login_required
def publish_sequence(request, sequence_id):
    """
    Allows an inspector to publish a specific sequence. 
    If all sequences in the chapter are published, the chapter is published too.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if request.user.groups.filter(name='Inspecteur').exists():
        if sequence.status == 'CONTENT_VALIDATED':
            sequence.status = 'PUBLISHED'
            sequence.save()
            
            chapter = sequence.chapter
            
            # Check if all sequences in the chapter are now published
            all_published = True
            for seq in chapter.sequences.all():
                if seq.status != 'PUBLISHED':
                    all_published = False
                    break
            
            if all_published:
                chapter.status = 'PUBLISHED'
                chapter.save()
                messages.success(request, f"La séquence '{sequence.name}' a été publiée. Toutes les séquences du chapitre étant publiées, le chapitre '{chapter.name}' est désormais publié.")
            else:
                messages.success(request, f"La séquence '{sequence.name}' a été publiée. Le chapitre est en attente de publication des autres séquences.")
                
    return redirect('inspector_dashboard')