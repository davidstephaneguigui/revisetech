from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from pedagogy.models import Matiere, Sequence, Activity, Choice
from classroom.models import Suggestion
from .models import Result, Badge

import json


@login_required
def student_home(request):
    """
    Display the main dashboard for students, showing only subjects 
    associated with their classes and unread suggestions.
    """
    student_classes = request.user.student_classes.all()
    
    # Find all sequences assigned to these classes AND that are published
    assigned_sequences = Sequence.objects.filter(classes__in=student_classes, status='PUBLISHED').distinct()
    
    # Find the subjects that contain these sequences
    subjects = Matiere.objects.filter(chapters__sequences__in=assigned_sequences).distinct()
    
    # Fetch unread suggestions for the student
    suggestions = Suggestion.objects.filter(student=request.user, is_read=False).order_by('-created_at')
    
    context = {
        'subjects': subjects,
        'suggestions': suggestions
    }
    
    return render(request, 'learning/student_home.html', context)


@login_required
def student_progression(request):
    """
    Display the student's progression, including badges and average scores.
    """
   
    badges = Badge.objects.filter(student=request.user).order_by('-date_obtained')
    
    student_classes = request.user.student_classes.all()
    # Calculate total badges available (only published sequences)
    total_sequences = Sequence.objects.filter(classes__in=student_classes, status='PUBLISHED').distinct().count()
    
    context = {
        'badges': badges,
        'total_sequences': total_sequences,
    }
    
    return render(request, 'learning/progression.html', context)


@require_POST
@login_required
def api_submit_quiz(request, activity_id):
    try:
        data = json.loads(request.body)
        answers = data.get('answers', {}) # Dictionnaire {question_id: choice_id}
        
        activity = get_object_or_404(Activity, id=activity_id)
        questions = activity.questions.all()
        
        score = 0
        max_score = questions.count()
        
        # Calcul du score
        for q in questions:
            selected_choice_id = answers.get(str(q.id))
            if selected_choice_id:
                try:
                    choice = q.choices.get(id=selected_choice_id)
                    if choice.is_correct:
                        score += 1
                except Choice.DoesNotExist:
                    pass

        # Enregistrement du résultat en base
        Result.objects.create(
            student=request.user,
            activity=activity,
            score=score,
            max_score=max_score
        )

        # --- LOGIQUE DES BADGES (reprise de l'ancienne vue) ---
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

        return JsonResponse({'status': 'success', 'score': score, 'max_score': max_score})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)