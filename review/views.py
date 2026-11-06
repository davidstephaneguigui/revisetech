from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pedagogy.models import Sequence, Session
from django.db.models import Q


@login_required
def submit_sequence(request, sequence_id):
    """
    Allows the designer to submit a sequence for validation.
    """
    # Remplace l'ancienne ligne par celle-ci :
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    
    if sequence.status == 'DRAFT':
        sequence.status = 'PENDING'
        sequence.save()
        messages.success(request, "La séquence a été soumise pour validation.")
    
    return redirect('manage_sequence', sequence_id=sequence.id)


@login_required
def referee_dashboard(request):
    """
    Display the dashboard for referees, showing pending and validated sequences.
    """
    pending_sequences = Sequence.objects.filter(status='PENDING').order_by('chapter__matiere__name', 'name')
    validated_sequences = Sequence.objects.filter(status='VALIDATED').order_by('-id') # Most recent first
    
    context = {
        'pending_sequences': pending_sequences,
        'validated_sequences': validated_sequences
    }
    
    return render(request, 'review/referee_home.html', context)


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
            
            # Generate real Sessions from PlannedSessions
            planned_sessions = sequence.planned_sessions.all().order_by('order')
            for planned in planned_sessions:
                Session.objects.create(
                    sequence=sequence,
                    order=planned.order,
                    name=planned.name,
                    objective=planned.objective,
                    session_type=planned.session_type,
                    status='DRAFT'
                )
            
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
    Allows a referee to cancel a validation and send the sequence back to draft.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if request.user.groups.filter(name='Référent').exists():
        if sequence.status == 'VALIDATED':
            sequence.status = 'DRAFT'
            sequence.save()
            messages.warning(request, f"La validation de la séquence '{sequence.name}' a été annulée. Elle est repassée en brouillon.")
            
    return redirect('referee_dashboard')