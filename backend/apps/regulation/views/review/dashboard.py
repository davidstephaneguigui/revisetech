from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.accounts.decorators import is_referee
from apps.pedagogy.models import Chapter, Sequence


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

