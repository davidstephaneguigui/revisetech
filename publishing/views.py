from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from pedagogy.models import Sequence
from accounts.decorators import is_supervisor 
from django.contrib.auth import get_user_model
from classroom.models import Classe
from classroom.utils import compute_sequence_stats

@login_required
@is_supervisor
def supervisor_dashboard(request):
    """
    Display the dashboard for supervisors.
    """
    # Sequences in preparation (intention validated, content being filled)
    sequences_in_preparation = Sequence.objects.filter(status='VALIDATED').order_by('-id')
    #sequences_in_preparation = Sequence.objects.filter(status='VALIDATED').order_by('chapter__matiere__name', 'name')
   
    # Sequences ready for publication
    sequences_to_publish = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=False).order_by('-id')
    #sequences_to_publish = Sequence.objects.filter(status='CONTENT_VALIDATED').order_by('chapter__matiere__name', 'chapter__name', 'name')
    
    # Published sequences
    published_sequences = Sequence.objects.filter(status='PUBLISHED').order_by('-id')
    #published_sequences = Sequence.objects.filter(status='PUBLISHED').order_by('chapter__matiere__name', 'chapter__name', 'name')
    
    # Need Second review sequences
    second_reviews = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=True).order_by('-id')

    context = {
        'sequences_in_preparation': sequences_in_preparation,
        'sequences_to_publish': sequences_to_publish,
        'published_sequences': published_sequences,
        'second_reviews': second_reviews,
        'open_section': request.GET.get('section', ''),
    }
    
    return render(request, 'publishing/supervisor_home.html', context)


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
            
    return redirect('supervisor_dashboard')


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
            
    return redirect('supervisor_dashboard')


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
    return redirect('supervisor_dashboard')


@login_required
def sequence_stats(request, sequence_id):
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    # Sécurité : accessible aux Enseignants, Référents, Superviseurs
    user = request.user
    if not (user.groups.filter(name__in=['Enseignant', 'Référent', 'Superviseur', 'Administrateur']).exists()):
        return redirect('dashboard_home')

    # Stats globales (toutes classes confondues)
    global_avg, global_min, global_max, global_count = compute_sequence_stats(sequence)

    # Stats par classe
    classes_stats = []
    for classe in sequence.classes.all():
        avg, min_s, max_s, count = compute_sequence_stats(sequence, classe)
        classes_stats.append({
            'classe': classe,
            'avg': avg,
            'min': min_s,
            'max': max_s,
            'count': count
        })

    context = {
        'sequence': sequence,
        'global_avg': global_avg,
        'global_min': global_min,
        'global_max': global_max,
        'global_count': global_count,
        'classes_stats': classes_stats,
    }
    return render(request, 'publishing/sequence_stats.html', context)