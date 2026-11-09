from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
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
    Display the dashboard for designers, organized by sequence status.
    """
    user_sequences = Sequence.objects.filter(creator=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        form = SequenceForm(request.POST)
        form.fields['chapter'].queryset = Chapter.objects.all()
        
        if form.is_valid():
            sequence = form.save(commit=False)
            sequence.creator = request.user
            sequence.save()
            messages.success(request, "La séquence a été créée avec succès.")
            return redirect('designer_dashboard')
    else:
        form = SequenceForm()
        form.fields['chapter'].queryset = Chapter.objects.all()
    
    context = {
        'drafts': user_sequences.filter(status='DRAFT'),
        'intent_pending': user_sequences.filter(status='PENDING'),
        'in_progress': user_sequences.filter(status='VALIDATED'),
        'content_pending': user_sequences.filter(status='CONTENT_PENDING'),
        'content_validated': user_sequences.filter(status='CONTENT_VALIDATED'),
        'published': user_sequences.filter(status='PUBLISHED'),
        'form': form,
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
                
                # Flag the sequence as having changes that need review, without blocking the designer
                sequence.has_unreviewed_changes = True
                sequence.save()

                
                
                messages.warning(request, "La séance a été ajoutée. Le référent sera notifié de cette modification lors de sa prochaine lecture.")
                return redirect('manage_sequence', sequence_id=sequence.id)

    review_actions = sequence.review_actions.all()    
    
    context = {
        'sequence': sequence,
        'sessions': sessions,
        'intention_form': intention_form,
        'planned_sessions_formset': planned_sessions_formset,
        'session_form': session_form,
        'review_actions' : review_actions,
    }
    
    return render(request, 'authoring/manage_sequence.html', context)


@require_POST
@login_required
@is_designer
def delete_sequence(request, sequence_id):
    """
    Allows the designer to delete a sequence ONLY if it is in DRAFT status.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    
    if sequence.status == 'DRAFT':
        sequence.delete()
        messages.success(request, "La séquence a été supprimée définitivement.")
        return redirect('designer_dashboard')
    else:
        messages.error(request, "Vous ne pouvez pas supprimer une séquence qui est déjà engagée dans le processus de validation.")
        return redirect('manage_sequence', sequence_id=sequence.id)


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
def edit_session(request, session_id):
    """
    Display and handle the editing of an existing session.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    
    if request.method == 'POST':
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, "La séance a été modifiée avec succès.")
            return redirect('manage_sequence', sequence_id=session.sequence.id)
    else:
        form = SessionForm(instance=session)
        
    context = {
        'session': session,
        'form': form,
    }
    
    return render(request, 'authoring/edit_session.html', context)


@require_POST
@login_required
@is_designer
def move_session(request, session_id, direction):
    """
    Moves a session up or down by swapping its order with its neighbor.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    
    if direction == 'up':
        # Find the session with the next smaller order
        neighbor = Session.objects.filter(sequence=session.sequence, order__lt=session.order).order_by('-order').first()
    else:
        # Find the session with the next larger order
        neighbor = Session.objects.filter(sequence=session.sequence, order__gt=session.order).order_by('order').first()
    
    if neighbor:
        # Swap orders
        session.order, neighbor.order = neighbor.order, session.order
        session.save()
        neighbor.save()
        
    return redirect('manage_sequence', sequence_id=session.sequence.id)


@require_POST
@login_required
@is_designer
def delete_session(request, session_id):
    """
    Deletes a session and renumbers the remaining sessions to avoid gaps.
    """
    session = get_object_or_404(Session, id=session_id, sequence__creator=request.user)
    sequence = session.sequence
    
    if session.status == 'DRAFT':
        session.delete()
        
        # Renumber the remaining sessions
        remaining_sessions = sequence.sessions.order_by('order')
        for index, sess in enumerate(remaining_sessions, start=1):
            if sess.order != index:
                sess.order = index
                sess.save()
                
        messages.success(request, "La séance a été supprimée et les numéros ont été mis à jour.")
    else:
        messages.error(request, "Vous ne pouvez pas supprimer une séance qui a déjà été validée.")
        
    return redirect('manage_sequence', sequence_id=sequence.id)


@login_required
@is_designer
def edit_activity(request, activity_id):
    """
    Display and handle the editing of an existing activity.
    """
    activity = get_object_or_404(Activity, id=activity_id, sessions__sequence__creator=request.user)
    
    if request.method == 'POST':
        form = ActivityForm(request.POST, request.FILES, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "L'activité a été modifiée avec succès.")
            return redirect('manage_session', session_id=activity.sessions.first().id)
    else:
        form = ActivityForm(instance=activity)
        
    context = {
        'activity': activity,
        'form': form,
    }
    
    return render(request, 'authoring/edit_activity.html', context)


@login_required
@is_designer
def manage_quiz_questions(request, activity_id):
    """
    Display the questions of a quiz and handle adding a new one.
    """
    activity = get_object_or_404(Activity, id=activity_id, sessions__sequence__creator=request.user)
    
    if activity.activity_type != 'QUIZ':
        messages.error(request, "Cette activité n'est pas un quiz.")
        return redirect('manage_session', session_id=activity.sessions.first().id)
    
    # Calculate the next order number
    last_question = activity.questions.order_by('-order').first()
    next_order = (last_question.order + 1) if last_question else 1
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            # 1. Save the question
            question = form.save(commit=False)
            question.activity = activity
            question.save()
            
            # 2. Save the choices
            correct_choice = request.POST.get('correct_choice')
            
            for i in range(1, 5): # Loop from 1 to 4
                choice_text = request.POST.get(f'choice_{i}', '').strip()
                if choice_text: # Only save if the text is not empty
                    is_correct = (str(i) == correct_choice)
                    Choice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=is_correct
                    )
            
            messages.success(request, "La question et ses choix ont été ajoutés avec succès.")
            return redirect('manage_quiz_questions', activity_id=activity.id)
    else:
        # Pre-fill the order field with the next number
        form = QuestionForm(initial={'order': next_order})
        
    context = {
        'activity': activity,
        'questions': activity.questions.all(),
        'form': form,
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


@require_POST
@login_required
@is_designer
def delete_question(request, question_id):
    """
    Delete a specific question and its choices.
    """
    question = get_object_or_404(Question, id=question_id, activity__sessions__sequence__creator=request.user)
    activity_id = question.activity.id
    question.delete()
    messages.success(request, "La question a été supprimée.")
    return redirect('manage_quiz_questions', activity_id=activity_id)