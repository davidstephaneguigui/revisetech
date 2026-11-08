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