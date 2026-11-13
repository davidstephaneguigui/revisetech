from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import is_designer
from apps.pedagogy.models import (
    Activity,
    Choice,
    Question,
)

from ..forms import (
    ActivityForm,
    ChoiceForm,
    QuestionForm,
)


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

