from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import inlineformset_factory
from pedagogy.models import Matiere, Chapter, Sequence, Session, PlannedSession, Activity, Question, Choice
from .forms import QuestionForm, ChoiceForm
from django.contrib import messages
from accounts.decorators import is_designer
from .forms import SequenceForm, SessionForm, ActivityForm, SequenceIntentionForm, PlannedSessionForm, QuestionForm, ChoiceForm


@login_required
@is_designer
def designer_dashboard(request):
    """
    Display the dashboard for designers.
    - Shows sequences created by the designer.
    - Allows creating a sequence in ANY existing chapter.
    """
    # Fetch subjects created by this designer
    subjects = Matiere.objects.filter(creator=request.user)
    
    # Fetch all chapters from the database (to allow creating sequences anywhere)
    all_chapters = Chapter.objects.all().order_by('matiere__name', 'name')
    
    # Fetch sequences created by this specific designer
    sequences = Sequence.objects.filter(creator=request.user).order_by('chapter__name', 'name')
    
    if request.method == 'POST':
        form = SequenceForm(request.POST)
        form.fields['chapter'].queryset = all_chapters
        
        if form.is_valid():
            sequence = form.save(commit=False)
            sequence.creator = request.user # Assign the current user as the creator
            sequence.save()
            messages.success(request, "La séquence a été créée avec succès.")
            return redirect('designer_dashboard')
    else:
        form = SequenceForm()
        form.fields['chapter'].queryset = all_chapters
    
    context = {
        'subjects': subjects,
        'chapters': all_chapters,
        'sequences': sequences,
        'form': form
    }
    
    return render(request, 'authoring/designer_home.html', context)


@login_required
@is_designer
def manage_sequence(request, sequence_id):
    """
    Display the sequence details and handle intention submission or session creation.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    sessions = sequence.sessions.all()
    
    PlannedSessionFormSet = inlineformset_factory(
        Sequence, 
        PlannedSession, 
        form=PlannedSessionForm, 
        extra=1, 
        can_delete=True
    )
    
    intention_form = SequenceIntentionForm(instance=sequence)
    planned_sessions_formset = PlannedSessionFormSet(instance=sequence)
    session_form = SessionForm()
    
    if request.method == 'POST':
        # 1. Handle intention submission
        if 'save_intention' in request.POST or 'submit_intention' in request.POST:
            intention_form = SequenceIntentionForm(request.POST, instance=sequence)
            planned_sessions_formset = PlannedSessionFormSet(request.POST, instance=sequence)
            
            if intention_form.is_valid() and planned_sessions_formset.is_valid():
                seq = intention_form.save(commit=False)
                if 'submit_intention' in request.POST:
                    seq.status = 'PENDING'
                    messages.success(request, "La séquence a été soumise pour validation.")
                else:
                    messages.success(request, "Les caractéristiques ont été enregistrées.")
                seq.save()
                planned_sessions_formset.save()
                return redirect('manage_sequence', sequence_id=sequence.id)
                
        # 2. Handle adding a new session after intention validation
        elif 'add_session' in request.POST:
            session_form = SessionForm(request.POST)
            if session_form.is_valid():
                session = session_form.save(commit=False)
                session.sequence = sequence
                
                # Auto-increment the order
                last_session = sequence.sessions.order_by('-order').first()
                session.order = (last_session.order + 1) if last_session else 1
                session.save()
                
                # Change sequence status back to PENDING to notify the referee
                sequence.status = 'PENDING'
                sequence.save()
                
                messages.warning(request, "La séance a été ajoutée. La séquence a été renvoyée au référent pour valider cette nouvelle structure.")
                return redirect('manage_sequence', sequence_id=sequence.id)
    
    context = {
        'sequence': sequence,
        'sessions': sessions,
        'intention_form': intention_form,
        'planned_sessions_formset': planned_sessions_formset,
        'session_form': session_form,
    }
    
    return render(request, 'authoring/manage_sequence.html', context)


@login_required
@is_designer
def manage_session(request, session_id):
    """
    Display the activities of a specific session and handle activity creation.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    activities = session.activities.all()
    
    if request.method == 'POST':
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.save()
            activity.sessions.add(session)
            messages.success(request, "L'activité a été créée avec succès.")
            return redirect('manage_session', session_id=session.id)
    else:
        form = ActivityForm()
    
    context = {
        'session': session,
        'activities': activities,
        'form': form
    }
    
    return render(request, 'authoring/manage_session.html', context)


@login_required
@is_designer
def delete_session(request, session_id):
    """
    Allows the designer to delete a session (and its activities).
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    sequence_id = session.sequence.id
    
    # Only allow deletion if the sequence is not in a pending validation state
    if session.sequence.status in ['VALIDATED', 'DRAFT']:
        session.delete()
        messages.success(request, "La séance a été supprimée avec succès.")
    else:
        messages.error(request, "Vous ne pouvez pas supprimer une séance dont le contenu est en cours de validation ou validé.")
        
    return redirect('manage_sequence', sequence_id=sequence_id)


@login_required
@is_designer
def manage_quiz_questions(request, activity_id):
    """
    Display and handle the questions and choices for a specific quiz activity.
    """
    activity = get_object_or_404(Activity, id=activity_id, sessions__sequence__creator=request.user)
    
    # Security check: Only for QUIZ activities
    if activity.activity_type != 'QUIZ':
        messages.error(request, "Cette activité n'est pas un quiz.")
        return redirect('manage_session', session_id=activity.sessions.first().id)
    
    # Create a formset for choices
    ChoiceFormSet = inlineformset_factory(
        Question, 
        Choice, 
        form=ChoiceForm, 
        extra=4, # 4 empty choices by default
        can_delete=True
    )
    
    # Create a formset for questions
    QuestionFormSet = inlineformset_factory(
        Activity,
        Question,
        form=QuestionForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        question_formset = QuestionFormSet(request.POST, instance=activity)
        if question_formset.is_valid():
            questions = question_formset.save()
            
            # Handle choices for each question (simplified approach)
            # In a real nested scenario, you'd handle the choice formsets in the template,
            # but for simplicity, we'll process them if they exist in the POST.
            
            messages.success(request, "Les questions ont été mises à jour avec succès.")
            return redirect('manage_quiz_questions', activity_id=activity.id)
    else:
        question_formset = QuestionFormSet(instance=activity)
        
    context = {
        'activity': activity,
        'question_formset': question_formset,
    }
    
    return render(request, 'authoring/manage_quiz_questions.html', context)


@login_required
@is_designer
def manage_question_choices(request, question_id):
    """
    Display and handle the choices (answers) for a specific question.
    """
    question = get_object_or_404(Question, id=question_id, activity__sessions__sequence__creator=request.user)
    
    ChoiceFormSet = inlineformset_factory(
        Question, 
        Choice, 
        form=ChoiceForm, 
        extra=4, # Show 4 empty slots by default
        can_delete=True
    )
    
    if request.method == 'POST':
        formset = ChoiceFormSet(request.POST, instance=question)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Les choix ont été enregistrés avec succès.")
            return redirect('manage_quiz_questions', activity_id=question.activity.id)
    else:
        formset = ChoiceFormSet(instance=question)
        
    context = {
        'question': question,
        'formset': formset,
    }
    
    return render(request, 'authoring/manage_question_choices.html', context)