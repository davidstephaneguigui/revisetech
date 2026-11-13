from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer, is_teacher
from apps.pedagogy.models import (
    Activity,
    Chapter,
    Choice,
    PlannedSession,
    Question,
    Sequence,
    Session,
)

from ..forms import (
    ActivityForm,
    ChoiceForm,
    PlannedSessionForm,
    QuestionForm,
    SequenceForm,
    SequenceIntentionForm,
    SessionForm,
)
from ..models import ActivityProposal

@login_required
@is_designer
def designer_dashboard(request):
    open_status = request.GET.get('status', '')
    
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

    chapters = Chapter.objects.all().order_by('name')
    user_sequences = Sequence.objects.filter(creator=request.user).order_by('name')

    # Application du filtre métier
    if open_status == 'INTENTIONS':
        user_sequences = user_sequences.filter(status__in=['DRAFT', 'PENDING'])
    elif open_status == 'IN_PROGRESS':
        user_sequences = user_sequences.filter(status__in=['VALIDATED', 'CONTENT_PENDING'])
    elif open_status == 'VALIDATED':
        user_sequences = user_sequences.filter(status='CONTENT_VALIDATED')
    elif open_status == 'PUBLISHED':
        user_sequences = user_sequences.filter(status='PUBLISHED')

    chapter_tabs = []
    for chapter in chapters:
        seqs = user_sequences.filter(chapter=chapter)
        if seqs.exists() or not open_status:
            chapter_tabs.append({
                'chapter': chapter,
                'sequences': seqs,
                'is_empty': seqs.count() == 0
            })

    context = {
        'chapter_tabs': chapter_tabs,
        'form': form,
        'chapters': Chapter.objects.all(),
        'pending_proposals_count': ActivityProposal.objects.filter(status='PENDING').count(),
        'open_status': open_status,
    }
    
    return render(request, 'authoring/designer_home.html', context)

