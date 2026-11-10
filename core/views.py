from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from pedagogy.models import Sequence
from classroom.models import Classe, Suggestion
from learning.models import Result


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
        context['second_reviews'] = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=True).count()
        context['published'] = Sequence.objects.filter(status='PUBLISHED').count()

    elif user.groups.filter(name='Référent').exists():
        context['role'] = 'Référent'
        context['pending_intentions'] = Sequence.objects.filter(status='PENDING').count()
        context['pending_contents'] = Sequence.objects.filter(status='CONTENT_PENDING').count()
        context['second_reviews'] = Sequence.objects.filter(status='CONTENT_VALIDATED', needs_second_review=True).count()
        context['published'] = Sequence.objects.filter(status='PUBLISHED').count()

    elif user.groups.filter(name='Concepteur').exists():
        context['role'] = 'Concepteur'
        user_sequences = Sequence.objects.filter(creator=user)
        context['drafts'] = user_sequences.filter(status='DRAFT').count()
        context['in_progress'] = user_sequences.filter(status='VALIDATED').count()
        context['validated'] = user_sequences.filter(status__in=['PENDING', 'CONTENT_PENDING', 'CONTENT_VALIDATED']).count()
        context['published'] = user_sequences.filter(status='PUBLISHED').count()

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
    """
    Display the general help and documentation page.
    """
    return render(request, 'core/help.html')