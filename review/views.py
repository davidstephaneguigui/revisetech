from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pedagogy.models import Sequence


@login_required
def submit_sequence(request, sequence_id):
    """
    Allows the designer to submit a sequence for validation.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, chapter__matiere__teacher=request.user)
    
    if sequence.status == 'DRAFT':
        sequence.status = 'PENDING'
        sequence.save()
        messages.success(request, "La séquence a été soumise pour validation.")
    
    return redirect('manage_sequence', sequence_id=sequence.id)


@login_required
def referee_dashboard(request):
    """
    Display the dashboard for referees, showing sequences pending validation.
    """
    pending_sequences = Sequence.objects.filter(status='PENDING').order_by('chapter__matiere__name', 'name')
    
    context = {
        'pending_sequences': pending_sequences
    }
    
    return render(request, 'review/referee_home.html', context)


@login_required
def validate_sequence(request, sequence_id):
    """
    Allows a referee to validate a sequence.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    if request.user.groups.filter(name='Référent').exists():
        sequence.status = 'VALIDATED'
        sequence.save()
        messages.success(request, f"La séquence '{sequence.name}' a été validée.")
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