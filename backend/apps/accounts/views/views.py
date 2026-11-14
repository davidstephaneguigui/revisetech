from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def dashboard_redirect(request):
    """
    Redirects users to their specific dashboard based on their group.
    """
    user = request.user
    
    if user.groups.filter(name='Enseignant').exists():
        return redirect('teacher_dashboard')
    elif user.groups.filter(name='Concepteur').exists():
        return redirect('designer_dashboard')
    elif user.groups.filter(name='Référent').exists():
        return redirect('referee_dashboard')
    elif user.groups.filter(name='Superviseur').exists():
            return redirect('supervisor_dashboard')
    elif user.groups.filter(name='Administrateur').exists():
        return redirect('/admin/')
    else:
        # Default to student home
        return redirect('student_home')
