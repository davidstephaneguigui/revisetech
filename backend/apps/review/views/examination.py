from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer, is_referee
from apps.pedagogy.models import Chapter, Sequence, Session

from ..forms import DevalidationForm


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

