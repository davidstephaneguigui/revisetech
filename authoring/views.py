from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pedagogy.models import Matiere, Chapter, Sequence, Session
from .forms import SequenceForm, SessionForm, ActivityForm

@login_required
def designer_dashboard(request):
    """
    Display the dashboard for designers, showing their subjects, chapters, 
    and sequences, and handle sequence creation.
    """
    subjects = Matiere.objects.filter(teacher=request.user)
    chapters = Chapter.objects.filter(matiere__in=subjects).order_by('matiere__name', 'name')
    sequences = Sequence.objects.filter(chapter__in=chapters).order_by('chapter__name', 'name')
    
    if request.method == 'POST':
        form = SequenceForm(request.POST)
        form.fields['chapter'].queryset = chapters
        
        if form.is_valid():
            form.save()
            messages.success(request, "La séquence a été créée avec succès.")
            return redirect('designer_dashboard')
    else:
        form = SequenceForm()
        form.fields['chapter'].queryset = chapters
    
    context = {
        'subjects': subjects,
        'chapters': chapters,
        'sequences': sequences,
        'form': form
    }
    
    return render(request, 'authoring/designer_home.html', context)

@login_required
def manage_sequence(request, sequence_id):
    """
    Display the sessions of a specific sequence and handle session creation.
    """
    sequence = get_object_or_404(Sequence, id=sequence_id, chapter__matiere__teacher=request.user)
    sessions = sequence.sessions.all()
    
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.sequence = sequence
            session.save()
            messages.success(request, "La séance a été créée avec succès.")
            return redirect('manage_sequence', sequence_id=sequence.id)
    else:
        form = SessionForm()
    
    context = {
        'sequence': sequence,
        'sessions': sessions,
        'form': form
    }
    
    return render(request, 'authoring/manage_sequence.html', context)

@login_required
def manage_session(request, session_id):
    """
    Display the activities of a specific session and handle activity creation.
    """
    session = get_object_or_404(Session, id=session_id, sequence__chapter__matiere__teacher=request.user)
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