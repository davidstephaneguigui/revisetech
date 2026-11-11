from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from accounts.decorators import get_user_roles
from .models import Matiere, Chapter, Sequence, Session, Activity, Choice
from classroom.models import ActivitySelection
from classroom.models import Suggestion
from learning.models import Result, Badge
from django.db.models import Q


def can_view_unpublished(user):
    """
    Returns True if the user is allowed to see unpublished content.
    Students (and anonymous users) are not allowed.
    """
    if not user.is_authenticated:
        return False
    # Staff and superusers can always see unpublished content
    if user.is_staff or user.is_superuser:
        return True
    
    # Teachers, designers, referees, supervisors can see unpublished content
    user_roles = get_user_roles(user)
    privileged_roles = {'Enseignant', 'Concepteur', 'Référent', 'Superviseur', 'Administrateur'}
    return bool(user_roles & privileged_roles)


@login_required
def mark_suggestion_read(request, suggestion_id):
    """
    Marks a suggestion as read and redirects the student to the activity.
    """
    suggestion = get_object_or_404(Suggestion, id=suggestion_id, student=request.user)
    suggestion.is_read = True
    suggestion.save()
    return redirect('activity_detail', activity_id=suggestion.activity.id)


@login_required
def subject_detail(request, subject_id):
    """
    Display the chapters (modules) of a specific subject.
    """
    subject = get_object_or_404(Matiere, id=subject_id)
    
    # Check if the user has the right to see unpublished chapters
    if can_view_unpublished(request.user):
        chapters = subject.chapters.all()
    else:
        # Students only see published chapters
        chapters = subject.chapters.filter(status='PUBLISHED')
        
    context = {
        'subject': subject,
        'chapters': chapters
    }
    
    return render(request, 'pedagogy/subject_detail.html', context)


@login_required
def chapter_detail(request, chapter_id):
    """
    Display the sequences of a specific chapter.
    """
    chapter = get_object_or_404(Chapter, id=chapter_id)
    
    # Security check: Students cannot access unpublished chapters
    if not can_view_unpublished(request.user) and chapter.status != 'PUBLISHED':
        raise Http404("Ce chapitre n'est pas encore publié.")
    
    if can_view_unpublished(request.user):
        sequences = chapter.sequences.all()
    else:
        # Students only see published sequences
        sequences = chapter.sequences.filter(status='PUBLISHED')
        
    context = {
        'chapter': chapter,
        'sequences': sequences
    }
    
    return render(request, 'pedagogy/chapter_detail.html', context)


@login_required
def sequence_detail(request, sequence_id):
    """
    Display the sessions of a specific sequence.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    # Security check: Students cannot access unpublished sequences
    if not can_view_unpublished(request.user) and sequence.status != 'PUBLISHED':
        raise Http404("Cette séquence n'est pas encore publiée.")
    
    if can_view_unpublished(request.user):
        sessions = sequence.sessions.all()
    else:
        # Students only see published sessions
        sessions = sequence.sessions.filter(status='PUBLISHED')
        
    context = {
        'sequence': sequence,
        'sessions': sessions
    }
    
    return render(request, 'pedagogy/sequence_detail.html', context)


@login_required
def session_detail(request, session_id):
    """
    Display the activities of a specific session.
    """
    session = get_object_or_404(Session, id=session_id)
    
    # Security check: Students cannot access unpublished sessions
    if not can_view_unpublished(request.user) and session.status != 'PUBLISHED':
        raise Http404("Cette séance n'est pas encore publiée.")
    
    if can_view_unpublished(request.user):
        activities = session.activities.all()
    else:
        # --- NOUVELLE LOGIQUE POUR LES ÉLÈVES ---
        student_classes = request.user.student_classes.all()
        
        # 1. Récupérer les IDs des activités globales validées par les profs
        selected_global_ids = ActivitySelection.objects.filter(
            classe__in=student_classes, 
            is_used=True
        ).values_list('activity_id', flat=True)
        
        # 2. Filtrer les activités de la séance
        activities = session.activities.filter(
            Q(is_local=True, classe__in=student_classes) | 
            Q(is_local=False, id__in=selected_global_ids, status='PUBLISHED')
        ).distinct()
        
    context = {
        'session': session,
        'activities': activities
    }
    
    return render(request, 'pedagogy/session_detail.html', context)


@login_required
def activity_detail(request, activity_id):
    """
    Display the content of a specific activity and handle quiz submission.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    
    # Security check: Students cannot access unpublished activities
    if not can_view_unpublished(request.user) and activity.status != 'PUBLISHED':
        raise Http404("Cette activité n'est pas encore publiée.")
        
    # --- NOUVELLE SÉCURITÉ POUR LES ÉLÈVES ---
    if not can_view_unpublished(request.user):
        student_classes = request.user.student_classes.all()
        
        if activity.is_local:
            # Si c'est une activité locale, elle doit appartenir à une de ses classes
            if activity.classe not in student_classes:
                raise Http404("Vous n'avez pas accès à cette activité.")
        else:
            # Si c'est une activité globale, elle doit avoir été validée par un prof
            is_selected = ActivitySelection.objects.filter(
                classe__in=student_classes, 
                activity=activity, 
                is_used=True
            ).exists()
            if not is_selected:
                raise Http404("Vous n'avez pas accès à cette activité.")
            
    questions = None
    score = None
    
    # ... (Le reste de ta fonction reste inchangé à partir d'ici)
    if activity.activity_type == 'QUIZ':
        questions = activity.questions.prefetch_related('choices').all()
        
        if request.method == 'POST':
            score = 0
            for question in questions:
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    try:
                        selected_choice = question.choices.get(id=choice_id)
                        if selected_choice.is_correct:
                            score += 1
                    except Choice.DoesNotExist:
                        pass
            
            Result.objects.create(
                student=request.user,
                activity=activity,
                score=score,
                max_score=questions.count()
            )
            
            # --- BADGE LOGIC ---
            if activity.sessions.exists():
                sequence = activity.sessions.first().sequence
                sequence_quizzes = Activity.objects.filter(sessions__sequence=sequence, activity_type='QUIZ').distinct()
                
                total_best_score = 0
                total_max_score = 0
                has_done_all_quizzes = True
                
                for quiz in sequence_quizzes:
                    best_result = Result.objects.filter(student=request.user, activity=quiz).order_by('-score').first()
                    if best_result:
                        total_best_score += best_result.score
                        total_max_score += best_result.max_score
                    else:
                        has_done_all_quizzes = False
                        break
                
                if has_done_all_quizzes and total_max_score > 0:
                    average = total_best_score / total_max_score
                    if average >= 0.7:
                        Badge.objects.get_or_create(student=request.user, sequence=sequence)
                    else:
                        Badge.objects.filter(student=request.user, sequence=sequence).delete()
    
    context = {
        'activity': activity,
        'questions': questions,
        'score': score,
        'max_score': questions.count() if questions else 0
    }
    
    return render(request, 'pedagogy/activity_detail.html', context)