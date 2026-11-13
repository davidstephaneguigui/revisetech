from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages

from apps.classroom.utils import compute_sequence_stats
from apps.pedagogy.models import Chapter, Sequence
from apps.accounts.decorators import is_supervisor


@login_required
@is_supervisor
def supervisor_dashboard(request):
    # On met 'second_reviews' par défaut
    open_section = request.GET.get('section', 'second_reviews')
    
    chapters = Chapter.objects.all().order_by('name')
    chapter_tabs = []

    for chapter in chapters:
        seqs = Sequence.objects.filter(chapter=chapter)
        
        # Préparation des listes selon la section
        in_preparation = seqs.filter(status='VALIDATED') if open_section in ['', 'in_preparation'] else []
        to_publish = seqs.filter(status='CONTENT_VALIDATED', needs_second_review=False) if open_section in ['', 'to_publish'] else []
        second_reviews = seqs.filter(status='CONTENT_VALIDATED', needs_second_review=True) if open_section in ['', 'second_reviews'] else []
        published = seqs.filter(status='PUBLISHED') if open_section in ['', 'published'] else []
        
        total_actions = len(in_preparation) + len(to_publish) + len(second_reviews)
        
        if total_actions > 0 or len(published) > 0:
            chapter_tabs.append({
                'chapter': chapter,
                'in_preparation': in_preparation,
                'to_publish': to_publish,
                'second_reviews': second_reviews,
                'published': published,
                'total_actions': total_actions
            })

    chapter_tabs = sorted(chapter_tabs, key=lambda x: x['total_actions'], reverse=True)

    context = {
        'chapter_tabs': chapter_tabs,
        'open_section': open_section,
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


@login_required
def supervisor_sequence_exam(request, sequence_id):
    sequence = get_object_or_404(Sequence, id=sequence_id)
    exam_type = request.GET.get('type', 'to_publish')
    
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Espace Superviseur', 'url': reverse('supervisor_dashboard')},
        {'label': sequence.name, 'url': None}
    ]

    # On récupère les référents pour la demande de second avis
    # (On exclut le premier référent si possible, sinon on prend tous les référents)
    User = get_user_model()
    available_referees = User.objects.filter(groups__name='Référent')
    if sequence.first_referee:
        available_referees = available_referees.exclude(id=sequence.first_referee.id)

    context = {
        'sequence': sequence,
        'exam_type': exam_type,
        'breadcrumbs': breadcrumbs,
        'sessions': sequence.sessions.all().order_by('order'),
        'available_referees': available_referees,
    }
    return render(request, 'publishing/supervisor_sequence_exam.html', context)