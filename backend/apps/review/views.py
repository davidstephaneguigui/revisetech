from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer, is_referee
from apps.pedagogy.models import Chapter, Sequence, Session

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


@login_required
@is_referee
def referee_dashboard(request):
    # On récupère la section demandée (intentions par défaut)
    open_section = request.GET.get('section', 'intentions')
    
    chapters = Chapter.objects.all().order_by('name')
    chapter_tabs = []

    for chapter in chapters:
        seqs = Sequence.objects.filter(chapter=chapter)
        
        # On prépare les listes (vides si ce n'est pas la section demandée)
        pending_intentions = seqs.filter(status='PENDING').order_by('created_at') if open_section in ['', 'intentions'] else []
        pending_contents = seqs.filter(status='CONTENT_PENDING').order_by('created_at') if open_section in ['', 'contents'] else []
        second_reviews = seqs.filter(status='CONTENT_VALIDATED', needs_second_review=True).order_by('created_at') if open_section in ['', 'second_review'] else []
        published = seqs.filter(status='PUBLISHED').order_by('-id') if open_section in ['', 'published'] else []
        
        total_actions = len(pending_intentions) + len(pending_contents) + len(second_reviews)
        
        # On n'affiche le chapitre que s'il y a quelque chose à voir dans cette section
        if total_actions > 0 or len(published) > 0:
            chapter_tabs.append({
                'chapter': chapter,
                'pending_intentions': pending_intentions,
                'pending_contents': pending_contents,
                'second_reviews': second_reviews,
                'published': published,
                'total_actions': total_actions
            })

    # On trie pour que les chapitres avec le plus d'actions soient en premier
    chapter_tabs = sorted(chapter_tabs, key=lambda x: x['total_actions'], reverse=True)

    context = {
        'chapter_tabs': chapter_tabs,
        'open_section': open_section, # On passe la section au template
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


@login_required
@is_referee
def referee_chapter_detail(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    # Tri strict : Intentions (date), puis Contenus (date), puis 2ème avis
    pending_intentions = Sequence.objects.filter(chapter=chapter, status='PENDING').order_by('created_at')
    pending_contents = Sequence.objects.filter(chapter=chapter, status='CONTENT_PENDING').order_by('created_at')
    second_reviews = Sequence.objects.filter(chapter=chapter, status='CONTENT_VALIDATED', needs_second_review=True).order_by('created_at')
    published = Sequence.objects.filter(chapter=chapter, status='PUBLISHED').order_by('-id')

    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Espace Référent', 'url': reverse('referee_dashboard')},
        {'label': chapter.name, 'url': None}
    ]

    context = {
        'chapter': chapter,
        'pending_intentions': pending_intentions,
        'pending_contents': pending_contents,
        'second_reviews': second_reviews,
        'published': published,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'review/referee_chapter_detail.html', context)


@login_required
@is_referee
def referee_sequence_exam(request, sequence_id):
    sequence = get_object_or_404(Sequence, id=sequence_id)
    # On récupère le type depuis l'URL (par défaut 'content')
    exam_type = request.GET.get('type', 'content') 
    
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Espace Référent', 'url': reverse('referee_dashboard')},
        {'label': sequence.name, 'url': None}
    ]

    context = {
        'sequence': sequence,
        'exam_type': exam_type,
        'breadcrumbs': breadcrumbs,
    }
    
    # Si on valide une intention, on montre les séances prévisionnelles
    if exam_type == 'intention':
        context['planned_sessions'] = sequence.planned_sessions.all().order_by('order')
    # Sinon (contenu, second avis, publié), on montre les séances réelles
    else:
        context['sessions'] = sequence.sessions.all().order_by('order')

    return render(request, 'review/referee_sequence_exam.html', context)