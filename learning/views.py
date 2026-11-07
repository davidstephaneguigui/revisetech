from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Badge
from classroom.models import Suggestion
from pedagogy.models import Matiere, Sequence


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
    
    return render(request, 'learning/student_home.html', context)


@login_required
def student_progression(request):
    """
    Display the student's progression, including badges and average scores.
    """
    # Fetch badges obtained by the student
    badges = Badge.objects.filter(student=request.user).order_by('-date_obtained')
    
    # Calculate total badges available (total sequences in the student's classes)
    student_classes = request.user.student_classes.all()
    total_sequences = Sequence.objects.filter(chapter__matiere__classes__in=student_classes).distinct().count()
    
    context = {
        'badges': badges,
        'total_sequences': total_sequences,
    }
    
    return render(request, 'learning/progression.html', context)