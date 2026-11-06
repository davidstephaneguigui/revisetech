from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import inlineformset_factory
from pedagogy.models import Matiere, Chapter, Sequence, Session, PlannedSession
from .forms import SequenceForm, SessionForm, ActivityForm, SequenceIntentionForm, PlannedSessionForm

@login_required
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
def manage_sequence(request, sequence_id):
    """
    Display the sequence details and handle intention submission (with planned sessions) or session creation.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, creator=request.user)
    sessions = sequence.sessions.all()
    
    # Create the formset for planned sessions
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
        # Handle saving or submitting the intention + planned sessions
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
                
        # Handle creating a new real session (only if intention is validated)
        elif 'create_session' in request.POST:
            session_form = SessionForm(request.POST)
            if session_form.is_valid():
                session = session_form.save(commit=False)
                session.sequence = sequence
                # Auto-increment the order
                last_session = sequence.sessions.order_by('-order').first()
                session.order = (last_session.order + 1) if last_session else 1
                session.save()
                messages.success(request, "La séance a été créée avec succès.")
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