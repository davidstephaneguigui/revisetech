from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer
from apps.pedagogy.models import (
    Session,
)

from ..forms import (
    ActivityForm,
    SessionForm,
)


@login_required
@is_designer
def manage_session(request, session_id):
    """
    Display the activities of a specific session and handle activity creation.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    activities = session.activities.all()
    
    if request.method == 'POST':
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.save()
            activity.sessions.add(session)
            messages.success(request, "L'activité a été créée avec succès.")
            return redirect('manage_session', session_id=session.id)
    else:
        form = ActivityForm()
    
    context = {
        'session': session,
        'activities': activities,
        'form': form
    }
    
    return render(request, 'authoring/manage_session.html', context)


@login_required
@is_designer
def edit_session(request, session_id):
    """
    Display and handle the editing of an existing session.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "La séance a été modifiée avec succès.")
            return redirect('manage_sequence', sequence_id=session.sequence.id)
    else:
        form = SessionForm(instance=session)
        
    context = {
        'session': session,
        'form': form,
    }
    
    return render(request, 'authoring/edit_session.html', context)


@require_POST
@login_required
@is_designer
def move_session(request, session_id, direction):
    """
    Moves a session up or down by swapping its order with its neighbor.
    """
    from django.db import transaction
    
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    
    if direction == 'up':
        neighbor = Session.objects.filter(sequence=session.sequence, order__lt=session.order).order_by('-order').first()
    else:
        neighbor = Session.objects.filter(sequence=session.sequence, order__gt=session.order).order_by('order').first()
    
    if neighbor:
        with transaction.atomic():
            # On sauvegarde les ordres actuels
            current_order = session.order
            neighbor_order = neighbor.order
            
            # 1. On place la séance dans un ordre temporaire négatif (libre)
            session.order = -1
            session.save()
            
            # 2. On met le voisin à la place de la séance
            neighbor.order = current_order
            neighbor.save()
            
            # 3. On met la séance à la place du voisin
            session.order = neighbor_order
            session.save()
        
    return redirect('manage_sequence', sequence_id=session.sequence.id)


@require_POST
@login_required
@is_designer
def delete_session(request, session_id):
    """
    Deletes a session and renumbers the remaining sessions to avoid gaps.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    sequence = session.sequence
    
    if session.status == 'DRAFT':
        session.delete()
        
        # Renumber the remaining sessions
        remaining_sessions = sequence.sessions.order_by('order')
        for index, sess in enumerate(remaining_sessions, start=1):
            if sess.order != index:
                sess.order = index
                sess.save()
                
        messages.success(request, "La séance a été supprimée et les numéros ont été mis à jour.")
    else:
        messages.error(request, "Vous ne pouvez pas supprimer une séance qui a déjà été validée.")
        
    return redirect('manage_sequence', sequence_id=sequence.id)

