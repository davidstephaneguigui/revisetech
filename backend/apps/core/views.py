from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from apps.pedagogy.models import Chapter, Sequence
from apps.classroom.models import Classe, Suggestion
from apps.learning.models import Result


@login_required
def dashboard_home(request):
    """
    Central landing page that adapts its content based on the user's highest role.
    """
    user = request.user
    context = {}

    if user.groups.filter(name='Administrateur').exists():
        context['role'] = 'Administrateur'

    elif user.groups.filter(name='Superviseur').exists():
        context['role'] = 'Superviseur'
        context['in_preparation'] = Sequence.objects.filter(status='VALIDATED').count()
        context['to_publish'] = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=False).count()
        context['published'] = Sequence.objects.filter(status='PUBLISHED').count()
        # Ligne second_reviews supprimée

    elif user.groups.filter(name='Référent').exists():
        context['role'] = 'Référent'
        context['pending_intentions'] = Sequence.objects.filter(status='PENDING').count()
        context['pending_contents'] = Sequence.objects.filter(status='CONTENT_PENDING').count()
        context['published'] = Sequence.objects.filter(status='PUBLISHED').count()
        # Ligne second_reviews supprimée

    elif user.groups.filter(name='Concepteur').exists():
        context['role'] = 'Concepteur'
        user_sequences = Sequence.objects.filter(creator=user)
        
        # On regroupe les statuts selon la logique métier
        context['intentions_count'] = user_sequences.filter(status__in=['DRAFT', 'PENDING']).count()
        context['in_progress_count'] = user_sequences.filter(status__in=['VALIDATED', 'CONTENT_PENDING']).count()
        context['validated_count'] = user_sequences.filter(status='CONTENT_VALIDATED').count()
        context['published_count'] = user_sequences.filter(status='PUBLISHED').count()

    elif user.groups.filter(name='Enseignant').exists():
        context['role'] = 'Enseignant'
        context['classes_count'] = Classe.objects.filter(main_teacher=user).count()
        context['students_count'] = get_user_model().objects.filter(
            student_classes__main_teacher=user
        ).distinct().count()
        context['suggestions_count'] = Suggestion.objects.filter(teacher=user).count()
        context['results_count'] = Result.objects.filter(
            student__student_classes__main_teacher=user
        ).distinct().count()

    else:
        return redirect('student_home')

    return render(request, 'core/dashboard_home.html', context)


@login_required
def help_page(request):
    context = {}
    user = request.user
    
    # Détection du rôle pour adapter l'aide
    if user.groups.filter(name='Administrateur').exists():
        context['role'] = 'Administrateur'
    elif user.groups.filter(name='Superviseur').exists():
        context['role'] = 'Superviseur'
    elif user.groups.filter(name='Référent').exists():
        context['role'] = 'Référent'
    elif user.groups.filter(name='Concepteur').exists():
        context['role'] = 'Concepteur'
    elif user.groups.filter(name='Enseignant').exists():
        context['role'] = 'Enseignant'
    else:
        context['role'] = 'Élève'

    return render(request, 'core/help.html', context)


@login_required
def apprenticeship_stats(request):
    if not (request.user.groups.filter(name__in=['Référent', 'Superviseur']).exists()):
        return redirect('dashboard_home')

    # 1. Total des quiz réalisés
    total_results = Result.objects.count()

    # 2. Nombre d'élèves actifs (distinct)
    User = get_user_model()
    active_students = User.objects.filter(results__isnull=False).distinct().count()

    # 3. Moyenne globale (Option B : total points obtenus / total points possibles)
    all_results = Result.objects.all()
    total_obtained = sum(r.score for r in all_results)
    total_possible = sum(r.max_score for r in all_results)
    
    if total_possible > 0:
        global_average = (total_obtained / total_possible) * 5
    else:
        global_average = 0

    # 4. Statistiques générales (déjà présentes)
    total_sequences = Sequence.objects.filter(status='PUBLISHED').count()
    total_chapters = Chapter.objects.count()

    context = {
        'total_results': total_results,
        'active_students': active_students,
        'global_average': round(global_average, 1),
        'total_sequences': total_sequences,
        'total_chapters': total_chapters,
    }
    return render(request, 'core/apprenticeship_stats.html', context)