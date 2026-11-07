from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Matiere, Chapter, Sequence, Session, Activity, Choice
from classroom.models import Suggestion
from learning.models import Result, Badge


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
    chapters = subject.chapters.all()
    
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
    sequences = chapter.sequences.all()
    
    context = {
        'chapter': chapter,
        'sequences': sequences
    }
    
    return render(request, 'pedagogy/chapter_detail.html', context)


@login_required
def sequence_detail(request, sequence_id):
    """
    Display the sessions of a specific sequence
    """
    sequence = get_object_or_404(Sequence, id=sequence_id)
    sessions = sequence.sessions.all()

    context = {
        'sequence': sequence,
        'sessions': sessions
    }

    return render(request, 'pedagogy/sequence_detail.html', context)


@login_required
def session_detail(request, session_id):
    """
    Display the sessions of a specific sequence
    """
    session = get_object_or_404(Session, id=session_id)
    activities = session.activities.all()

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
    questions = None
    score = None
    
    if activity.activity_type == 'QUIZ':
        questions = activity.questions.prefetch_related('choices').all()
        
        if request.method == 'POST':
            score = 0
            for question in questions:
                # Get the submitted choice ID for this question
                choice_id = request.POST.get(f'question_{question.id}')
                if choice_id:
                    # Check if the selected choice is correct
                    try:
                        selected_choice = question.choices.get(id=choice_id)
                        if selected_choice.is_correct:
                            score += 1
                    except Choice.DoesNotExist:
                        pass # Invalid choice submitted
            
            # Save the result to the database
            Result.objects.create(
                student=request.user,
                activity=activity,
                score=score,
                max_score=questions.count()
            )

            # --- BADGE LOGIC ---
            if activity.activity_type == 'QUIZ' and activity.sessions.exists():
                # Get the sequence this quiz belongs to
                sequence = activity.sessions.first().sequence
                
                # Get all quiz activities in this sequence
                sequence_quizzes = Activity.objects.filter(sessions__sequence=sequence, activity_type='QUIZ').distinct()
                
                # Get the best score for each quiz for this student
                total_best_score = 0
                total_max_score = 0
                has_done_all_quizzes = True
                
                for quiz in sequence_quizzes:
                    best_result = Result.objects.filter(student=request.user, activity=quiz).order_by('-score').first()
                    if best_result:
                        total_best_score += best_result.score
                        total_max_score += best_result.max_score
                    else:
                        # The student hasn't done this quiz yet
                        has_done_all_quizzes = False
                        break
                
                # If the student has done all quizzes, calculate the average
                if has_done_all_quizzes and total_max_score > 0:
                    average = total_best_score / total_max_score
                    
                    # Check if average is >= 0.7 (which is 3.5/5 or 7/10)
                    if average >= 0.7:
                        # Give the badge (get_or_create avoids duplicate errors)
                        Badge.objects.get_or_create(student=request.user, sequence=sequence)
                    else:
                        # Revoke the badge if the average dropped
                        Badge.objects.filter(student=request.user, sequence=sequence).delete()

    
    context = {
        'activity': activity,
        'questions': questions,
        'score': score,
        'max_score': questions.count() if questions else 0,
        'from_sequence': request.GET.get('from_sequence', ''),
    }
    
    return render(request, 'pedagogy/activity_detail.html', context)
