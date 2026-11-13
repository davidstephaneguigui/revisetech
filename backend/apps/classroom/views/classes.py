from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_teacher
from apps.classroom.utils import compute_sequence_stats
from apps.learning.models import Result
from apps.pedagogy.models import Activity, Sequence, Session

from ..forms import (
    AddSequenceToClassForm,
    AddStudentForm,
    ClasseForm,
    JoinClassForm,
    LocalActivityForm,
    SuggestionForm,
)
from ..models import ActivitySelection, Classe, SessionCompletion, Suggestion
from ..utils import get_student_global_score


@login_required
@is_teacher
def teacher_results(request):
    # Sécurité : On ne récupère que les classes de l'enseignant connecté
    classes = Classe.objects.filter(main_teacher=request.user).order_by('name')
    
    # Préparation du fil d'Ariane
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Élèves', 'url': None}
    ]
    
    context = {
        'classes': classes,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/teacher_results.html', context)


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
    
    # =========================================================
    # NOUVEAU : Calcul des statistiques pour chaque séquence
    # =========================================================
    available_sequences = Sequence.objects.filter(status='PUBLISHED')
    sequences_data = []
    
    for seq in available_sequences:
        # On utilise le helper pour avoir la moyenne globale (toutes classes confondues)
        avg, min_s, max_s, count = compute_sequence_stats(seq)
        
        # On convertit la moyenne sur 20 en pourcentage de réussite
        if avg is not None:
            success_rate = int((avg / 20) * 100)
        else:
            success_rate = None
            
        sequences_data.append({
            'sequence': seq,
            'rate': success_rate,
            'count': count
        })
    
    context = {
        'classe': classe,
        'students': students,
        'sequence_form': sequence_form,
        'student_form': student_form,
        'class_sequences': classe.sequences.all(),
        'sequences_data': sequences_data, # <-- On passe la liste au template
    }
    
    return render(request, 'classroom/class_detail.html', context)


@login_required
@is_teacher
def class_sequence_detail(request, class_id, sequence_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    if sequence not in classe.sequences.all():
        return redirect('class_detail', class_id=classe.id)
        
    # On crée les suivis manquants sans casser l'ordre existant
    for sess in sequence.sessions.all():
        SessionCompletion.objects.get_or_create(classe=classe, session=sess)

    # On récupère les séances triées
    completions = SessionCompletion.objects.filter(
        classe=classe, 
        session__in=sequence.sessions.all()
    ).order_by('order', 'id')
    
    sessions = [c.session for c in completions]
    
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Classes', 'url': reverse('teacher_results')},
        {'label': classe.name, 'url': reverse('class_detail', args=[classe.id])},
        {'label': sequence.name, 'url': None}
    ]

    context = {
        'classe': classe,
        'sequence': sequence,
        'sessions': sessions,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/class_sequence_detail.html', context)


@login_required
@is_teacher
def class_results(request, class_id):
    # Sécurité : On vérifie que la classe appartient bien à l'enseignant connecté
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    
    # On récupère les élèves triés par ordre alphabétique
    students = classe.students.all().order_by('username')
    
    # On prépare les données pour le template
    student_data = []
    for student in students:
        score, color = get_student_global_score(student)
        student_data.append({
            'student': student,
            'score': score,
            'color': color
        })
        
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Élèves', 'url': reverse('teacher_results')},
        {'label': classe.name, 'url': None}
    ]
    
    context = {
        'classe': classe,
        'student_data': student_data,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/class_results.html', context)


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

