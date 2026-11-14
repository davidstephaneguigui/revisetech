from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.decorators import is_supervisor
from apps.classroom.utils import compute_sequence_stats
from apps.pedagogy.models import Sequence


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
@is_supervisor
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