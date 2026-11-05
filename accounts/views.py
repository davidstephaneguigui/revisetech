from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from pedagogy.models import Matiere
from classroom.models import Classe
from learning.models import Result
from .forms import ClasseForm, JoinClassForm, AddSubjectToClassForm, SuggestionForm

@login_required
def teacher_dashboard(request):
    """
    Display the dashboard for teachers and handle class creation.
    """
    classes = Classe.objects.filter(main_teacher=request.user)
    form = ClasseForm()
    
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            classe = form.save(commit=False)
            classe.main_teacher = request.user # Assign the current user as the main teacher
            classe.save()
            return redirect('teacher_dashboard')
    
    context = {
        'classes': classes,
        'form': form
    }
    
    return render(request, 'accounts/teacher_home.html', context)


@login_required
def dashboard_redirect(request):
    """
    Redirects users to their specific dashboard based on their group.
    """
    user = request.user
    
    if user.groups.filter(name='Enseignant').exists():
        return redirect('teacher_dashboard')
    elif user.groups.filter(name='Concepteur').exists():
        return redirect('designer_dashboard')
    elif user.groups.filter(name='Référent').exists():
        return redirect('referee_dashboard')
    elif user.groups.filter(name='Administrateur').exists():
        return redirect('/admin/')
    else:
        # Default to student home
        return redirect('student_home')


@login_required
def class_detail(request, class_id):
    """
    Display the details of a specific class and handle adding subjects.
    """
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    students = classe.students.all()
    
    if request.method == 'POST':
        form = AddSubjectToClassForm(request.POST)
        # Only show subjects created by this specific teacher
        form.fields['matiere'].queryset = Matiere.objects.all()
        
        if form.is_valid():
            matiere = form.cleaned_data['matiere']
            classe.subjects.add(matiere)
            messages.success(request, f"La matière {matiere.name} a été ajoutée à la classe.")
            return redirect('class_detail', class_id=classe.id)
    else:
        form = AddSubjectToClassForm()
        form.fields['matiere'].queryset = Matiere.objects.all()
    
    context = {
        'classe': classe,
        'students': students,
        'form': form,
        'subjects': classe.subjects.all()
    }
    
    return render(request, 'accounts/class_detail.html', context)


@login_required
def join_class(request):
    """
    Allow a student to join a class using an invitation code.
    """
    form = JoinClassForm()
    
    if request.method == 'POST':
        form = JoinClassForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code_invitation'].upper()
            try:
                classe = Classe.objects.get(code_invitation=code)
                # Add the current user to the students of this class
                classe.students.add(request.user)
                messages.success(request, f"Tu as rejoint la classe {classe.name} !")
                return redirect('student_home')
            except Classe.DoesNotExist:
                form.add_error('code_invitation', "Ce code d'invitation n'est pas valide.")
    
    context = {
        'form': form
    }
    
    return render(request, 'accounts/join_class.html', context)


@login_required
def student_results(request, student_id):
    """
    Display the results of a specific student and handle sending suggestions.
    """
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    # Security check: Ensure the student is in at least one of the teacher's classes
    is_my_student = Classe.objects.filter(main_teacher=request.user, students=student).exists()
    if not is_my_student:
        messages.error(request, "Vous n'avez pas accès aux résultats de cet élève.")
        return redirect('teacher_dashboard')

    # Fetch all results for this student
    results = Result.objects.filter(student=student).order_by('-date_attempt')
    
    # Handle suggestion form submission
    if request.method == 'POST':
        form = SuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.teacher = request.user
            suggestion.student = student
            suggestion.save()
            messages.success(request, f"La suggestion a bien été envoyée à {student.username}.")
            return redirect('student_results', student_id=student.id)
    else:
        form = SuggestionForm()
    
    context = {
        'student': student,
        'results': results,
        'form': form
    }
    
    return render(request, 'accounts/student_results.html', context)
