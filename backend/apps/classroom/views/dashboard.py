from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.accounts.decorators import is_teacher

from ..forms import (
    ClasseForm,
)
from ..models import Classe


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
def teacher_preparations(request):
    breadcrumbs = [
        {'label': 'Accueil', 'url': reverse('dashboard_home')},
        {'label': 'Mes préparations', 'url': None}
    ]
    
    context = {
        'breadcrumbs': breadcrumbs
    }
    return render(request, 'classroom/teacher_preparations.html', context)