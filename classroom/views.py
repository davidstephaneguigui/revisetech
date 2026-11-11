from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from pedagogy.models import Sequence
from learning.models import Result
from .models import Classe, Suggestion, ActivitySelection
from .forms import ClasseForm, AddSequenceToClassForm, JoinClassForm, SuggestionForm, AddStudentForm
from accounts.decorators import is_teacher
from django.urls import reverse
from .utils import get_student_global_score
from django.http import HttpResponseForbidden
from classroom.utils import compute_sequence_stats
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import SessionCompletion

from pedagogy.models import Session
from .forms import LocalActivityForm


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
    
    # On vérifie que la séquence est bien assignée à cette classe
    if sequence not in classe.sequences.all():
        return redirect('class_detail', class_id=classe.id)
        
    sessions = sequence.sessions.all().order_by('order')
    
    # On prépare les données pour le template (comme sur la page class_results)
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Classes', 'url': reverse('teacher_dashboard')}, # ou teacher_results
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
def prepare_session(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    session = get_object_or_404(Session, id=session_id)
    
    # On récupère les activités globales (non locales)
    global_activities = session.activities.filter(is_local=False).order_by('id')
    
    # On récupère les activités locales créées par CET enseignant pour CETTE classe
    local_activities = session.activities.filter(is_local=True, classe=classe).order_by('id')
    
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Classes', 'url': reverse('teacher_results')},
        {'label': classe.name, 'url': reverse('class_detail', args=[classe.id])},
        {'label': session.sequence.name, 'url': reverse('class_sequence_detail', args=[classe.id, session.sequence.id])},
        {'label': session.name, 'url': None}
    ]
    
    context = {
        'classe': classe,
        'session': session,
        'global_activities': global_activities,
        'local_activities': local_activities,
        'breadcrumbs': breadcrumbs,
        'selected_activity_ids': list(classe.selected_activities.filter(is_used=True).values_list('activity_id', flat=True)),
    }
    return render(request, 'classroom/prepare_session.html', context)


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
@is_teacher
def student_profile(request, student_id):
    User = get_user_model()
    student = get_object_or_404(User, id=student_id)
    
    # Sécurité : Vérifier que l'élève est bien dans une classe de l'enseignant
    teacher_classes = Classe.objects.filter(main_teacher=request.user, students=student)
    if not teacher_classes.exists():
        return HttpResponseForbidden("Vous n'avez pas accès à cet élève.")
    
    classe = teacher_classes.first() # Pour le fil d'Ariane

    # 1. Historique complet des résultats
    results = Result.objects.filter(student=student).order_by('-id')

    # 2. Répartition par matière
    subjects_stats = {}
    for res in results:
        if not res.activity: continue
        try:
            # On remonte la chaîne pour trouver la matière
            matiere_name = res.activity.sessions.first().sequence.chapter.matiere.name
            if matiere_name not in subjects_stats:
                subjects_stats[matiere_name] = {'obtained': 0, 'total': 0}
            subjects_stats[matiere_name]['obtained'] += res.score
            subjects_stats[matiere_name]['total'] += res.activity.questions.count()
        except Exception:
            pass # Ignore si la chaîne de relation est incomplète
            
    subjects_breakdown = []
    for name, stats in subjects_stats.items():
        if stats['total'] > 0:
            avg = (stats['obtained'] / stats['total']) * 20
            subjects_breakdown.append({'name': name, 'average': round(avg, 1)})

    # 3. Les suggestions
    suggestions = Suggestion.objects.filter(student=student).order_by('-id')
    
    # Fil d'Ariane
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes Élèves', 'url': reverse('teacher_results')},
        {'label': classe.name, 'url': reverse('class_results', args=[classe.id])},
        {'label': student.username, 'url': None}
    ]

    context = {
        'student': student,
        'results': results,
        'subjects_breakdown': subjects_breakdown,
        'suggestions': suggestions,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/student_profile.html', context)


@require_POST
@login_required
@is_teacher
def toggle_session_completion(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    
    # On cherche ou on crée l'enregistrement
    completion, created = SessionCompletion.objects.get_or_create(
        classe=classe, 
        session_id=session_id
    )
    
    # On inverse l'état
    completion.is_completed = not completion.is_completed
    completion.save()
    
    # On renvoie une réponse JSON pour que le JS puisse mettre à jour l'icône sans recharger la page
    return JsonResponse({
        'status': 'success', 
        'is_completed': completion.is_completed
    })


@login_required
def create_local_activity(request, class_id, session_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    session = get_object_or_404(Session, id=session_id)
    
    if request.method == 'POST':
        form = LocalActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.is_local = True
            activity.creator = request.user
            activity.classe = classe
            activity.status = 'PUBLISHED'
            
            # 1. On sauvegarde d'abord l'activité en base de données
            activity.save() 
            
            # 2. On ajoute la séance à la relation ManyToMany
            activity.sessions.add(session)
            
            messages.success(request, "L'activité locale a été ajoutée à cette séance.")
            return redirect('prepare_session', class_id=classe.id, session_id=session.id)
    else:
        form = LocalActivityForm()

    return render(request, 'classroom/create_local_activity.html', {
        'form': form,
        'classe': classe,
        'session': session
    })


@require_POST
@login_required
@is_teacher
def toggle_activity_usage(request, class_id, activity_id):
    classe = get_object_or_404(Classe, id=class_id, main_teacher=request.user)
    
    selection, created = ActivitySelection.objects.get_or_create(
        classe=classe, 
        activity_id=activity_id
    )
    
    selection.is_used = not selection.is_used
    selection.save()
    
    return JsonResponse({'status': 'success', 'is_used': selection.is_used})