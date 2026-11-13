from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_supervisor
from apps.classroom.utils import compute_sequence_stats
from apps.pedagogy.models import Chapter, Sequence


@require_POST
@login_required
@is_supervisor
def publish_sequence(request, sequence_id):
    """
    Allows an supervisor to publish a specific sequence. 
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
            
    return redirect(reverse('supervisor_dashboard') + '?section=to_publish')


@require_POST
@login_required
@is_supervisor
def request_second_review(request, sequence_id):
    """
    Allows a supervisor to request a second review from another referee.
    The status remains CONTENT_VALIDATED but the flag is raised.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if sequence.status == 'CONTENT_VALIDATED':
        sequence.needs_second_review = True
        sequence.save()
        messages.success(request, f"Une seconde validation a été demandée pour la séquence '{sequence.name}'.")
            
    return redirect(reverse('supervisor_dashboard') + '?section=second_reviews')


@login_required
@require_POST
def unpublish_sequence(request, sequence_id):
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    # 1. La séquence retourne dans la file d'attente de publication
    sequence.status = 'CONTENT_VALIDATED'
    sequence.save()
    
    # 2. Cascade sur les séances et activités
    for session in sequence.sessions.all():
        session.status = 'DRAFT'
        session.save()
        for activity in session.activities.all():
            activity.status = 'DRAFT'
            activity.save()
            
    messages.warning(request, f"La séquence '{sequence.name}' a été dépubliée.")
    return redirect(reverse('supervisor_dashboard') + '?section=published')

