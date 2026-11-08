from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from pedagogy.models import Sequence
from learning.models import Result
from .models import Classe, Suggestion
from .forms import ClasseForm, AddSequenceToClassForm, JoinClassForm, SuggestionForm, AddStudentForm
from accounts.decorators import is_teacher

@login_required
@is_teacher
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
            classe.main_teacher = request.user
            classe.save()
            return redirect('teacher_dashboard')
    
    context = {
        'classes': classes,
        'form': form
    }
    
    return render(request, 'classroom/teacher_home.html', context)


@login_required
@is_teacher
def class_detail(request, class_id):
    """
    Display the details of a specific class and handle adding sequences or students.
    """
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    students = classe.students.all()
    
    sequence_form = AddSequenceToClassForm()
    student_form = AddStudentForm()
    
    if request.method == 'POST':
        # Check if the user is adding a student
        if 'add_student' in request.POST:
            student_form = AddStudentForm(request.POST)
            if student_form.is_valid():
                username = student_form.cleaned_data['username']
                User = get_user_model()
                try:
                    student = User.objects.get(username=username)
                    classe.students.add(student)
                    messages.success(request, f"L'élève {username} a été ajouté à la classe.")
                    return redirect('class_detail', class_id=classe.id)
                except User.DoesNotExist:
                    student_form.add_error('username', "Cet utilisateur n'existe pas.")
        
        # Check if the user is adding sequences
        elif 'add_sequences' in request.POST:
            sequence_form = AddSequenceToClassForm(request.POST)
            sequence_form.fields['sequences'].queryset = Sequence.objects.filter(status='PUBLISHED')
            if sequence_form.is_valid():
                sequences = sequence_form.cleaned_data['sequences']
                classe.sequences.add(*sequences)
                messages.success(request, "Les séquences ont été ajoutées à la classe.")
                return redirect('class_detail', class_id=classe.id)
                
    else:
        # For GET requests, populate the sequence form
        sequence_form.fields['sequences'].queryset = Sequence.objects.filter(status='PUBLISHED')
    
    context = {
        'classe': classe,
        'students': students,
        'sequence_form': sequence_form,
        'student_form': student_form,
        'class_sequences': classe.sequences.all()
    }
    
    return render(request, 'classroom/class_detail.html', context)


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
                classe.students.add(request.user)
                messages.success(request, f"Tu as rejoint la classe {classe.name} !")
                return redirect('student_home')
            except Classe.DoesNotExist:
                form.add_error('code_invitation', "Ce code d'invitation n'est pas valide.")
    
    context = {
        'form': form
    }
    
    return render(request, 'classroom/join_class.html', context)


@login_required
@is_teacher
def student_results(request, student_id):
    """
    Display the results of a specific student and handle sending suggestions.
    """
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    is_my_student = Classe.objects.filter(main_teacher=request.user, students=student).exists()
    if not is_my_student:
        messages.error(request, "Vous n'avez pas accès aux résultats de cet élève.")
        return redirect('teacher_dashboard')

    results = Result.objects.filter(student=student).order_by('-date_attempt')
    
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
    
    return render(request, 'classroom/student_results.html', context)


@login_required
def suggestion_list(request):
    """
    Display all suggestions received by the student.
    """
    # Fetch all suggestions for the student, most recent first
    suggestions = Suggestion.objects.filter(student=request.user).order_by('-created_at')
    
    # Mark all as read when the student opens the list
    unread_suggestions = suggestions.filter(is_read=False)
    unread_suggestions.update(is_read=True)
    
    context = {
        'suggestions': suggestions
    }
    
    return render(request, 'classroom/suggestion_list.html', context)