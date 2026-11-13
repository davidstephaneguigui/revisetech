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
def designer_proposals(request):
    # Vérifier que c'est bien un concepteur
    if not request.user.groups.filter(name='Concepteur').exists():
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('dashboard_home')
        
    proposals = ActivityProposal.objects.filter(status='PENDING').order_by('-created_at')
    return render(request, 'authoring/designer_proposals.html', {'proposals': proposals})


@require_POST
@login_required
def propose_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id, is_local=True)
    if activity.creator == request.user:
        if not ActivityProposal.objects.filter(activity=activity, status='PENDING').exists():
            ActivityProposal.objects.create(activity=activity, teacher=request.user)
            messages.success(request, "Votre activité a été proposée au concepteur.")
        else:
            messages.warning(request, "Cette activité est déjà en attente de validation.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_home'))


@require_POST
@login_required
def handle_proposal(request, proposal_id, action):
    if not request.user.groups.filter(name='Concepteur').exists():
        return redirect('dashboard_home')
        
    proposal = get_object_or_404(ActivityProposal, id=proposal_id)
    
    if action == 'accept':
        activity = proposal.activity
        
        # 1. On transforme l'activité locale en activité globale
        activity.is_local = False
        activity.classe = None # Elle n'appartient plus à une classe spécifique
        activity.status = 'PUBLISHED' # On s'assure qu'elle est publiée
        activity.save()
        
        # 2. On valide la proposition
        proposal.status = 'ACCEPTED'
        proposal.save()
        
        messages.success(request, f"L'activité '{activity.title}' a été promue au rang de référentiel global.")
        
    elif action == 'reject':
        proposal.status = 'REJECTED'
        proposal.save()
        messages.warning(request, "La proposition a été refusée.")
        
    return redirect('designer_proposals')


@login_required
@is_teacher
def activity_bank(request):
    # On récupère les activités globales qui ont été promues par un enseignant
    # (c'est-à-dire qui ont une proposition avec le statut ACCEPTED)
    promoted_activities = Activity.objects.filter(
        is_local=False, 
        authoring_proposals__status='ACCEPTED'
    ).distinct().order_by('-id')
    
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Banque des activités', 'url': None}
    ]
    
    context = {
        'promoted_activities': promoted_activities,
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'authoring/activity_bank.html', context)


