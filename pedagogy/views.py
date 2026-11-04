from django.shortcuts import render
from .models import Matiere

def student_home(request):
    """
    Display the main dashboard for students.
    Fetches all subjects to display them.
    """
    # Fetch all subjects from the database
    subjects = Matiere.objects.all()
    
    # Pass the subjects to the template via a context dictionary
    context = {
        'subjects': subjects
    }
    
    return render(request, 'pedagogy/student_home.html', context)