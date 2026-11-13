from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.decorators import is_supervisor
from apps.pedagogy.models import Chapter, Sequence


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

