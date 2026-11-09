from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def dashboard_home(request):
    """
    Central landing page for staff. Students are redirected to their learning space.
    """
    user = request.user
    context = {}
    
    if user.groups.filter(name='Administrateur').exists():
        context['role'] = 'Administrateur'
    elif user.groups.filter(name='Superviseur').exists():
        context['role'] = 'Superviseur'
    elif user.groups.filter(name='Référent').exists():
        context['role'] = 'Référent'
    elif user.groups.filter(name='Concepteur').exists():
        context['role'] = 'Concepteur'
    elif user.groups.filter(name='Enseignant').exists():
        context['role'] = 'Enseignant'
    else:
        # Students go straight to their mobile interface
        return redirect('student_home')

    return render(request, 'core/dashboard_home.html', context)


@login_required
def help_page(request):
    """
    Display the general help and documentation page.
    """
    return render(request, 'core/help.html')