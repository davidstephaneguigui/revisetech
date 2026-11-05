from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Matiere, Chapter, Sequence, Session, Activity, Suggestion, Choice, Result


@login_required
def student_home(request):
    """
    Display the main dashboard for students, showing only subjects 
    associated with their classes and unread suggestions.
    """
    student_classes = request.user.student_classes.all()
    subjects = Matiere.objects.filter(classes__in=student_classes).distinct()
    
    # Fetch unread suggestions for the student
    suggestions = Suggestion.objects.filter(student=request.user, is_read=False).order_by('-created_at')
    
    context = {
        'subjects': subjects,
        'suggestions': suggestions
    }
    
    return render(request, 'pedagogy/student_home.html', context)


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
    
    context = {
        'activity': activity,
        'questions': questions,
        'score': score,
        'max_score': questions.count() if questions else 0
    }
    
    return render(request, 'pedagogy/activity_detail.html', context)
