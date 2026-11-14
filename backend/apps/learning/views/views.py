import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.classroom.models import ActivitySelection, Suggestion
from apps.pedagogy.models import Activity, Choice, Matiere, Sequence
from apps.pedagogy.views.activities import can_view_unpublished

from ..models import Badge, Result


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
        answers = data.get('answers', {}) 
        
        activity = get_object_or_404(Activity, id=activity_id)
        
        # --- SÉCURITÉ 2.3 : Même logique que activity_detail ---
        if not can_view_unpublished(request.user) and activity.status != 'PUBLISHED':
            return JsonResponse({'status': 'error', 'message': 'Quiz non disponible.'}, status=403)
            
        if not can_view_unpublished(request.user):
            student_classes = request.user.student_classes.all()
            
            if activity.is_local:
                if activity.classe not in student_classes:
                    return JsonResponse({'status': 'error', 'message': 'Vous n\'avez pas accès à cette activité.'}, status=403)
            else:
                is_selected = ActivitySelection.objects.filter(
                    classe__in=student_classes, 
                    activity=activity, 
                    is_used=True
                ).exists()
                if not is_selected:
                    return JsonResponse({'status': 'error', 'message': 'Vous n\'avez pas accès à cette activité.'}, status=403)
        
        # --- Suite inchangée ---
        questions = activity.questions.all()
        score = 0
        max_score = questions.count()
        
        for q in questions:
            selected_choice_id = answers.get(str(q.id))
            if selected_choice_id:
                try:
                    choice = q.choices.get(id=selected_choice_id)
                    if choice.is_correct:
                        score += 1
                except Choice.DoesNotExist:
                    pass

        Result.objects.create(
            student=request.user,
            activity=activity,
            score=score,
            max_score=max_score
        )

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
        
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Une erreur est survenue lors de la soumission du quiz.'}, status=400)       