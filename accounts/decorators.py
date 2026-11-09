from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib.auth.views import redirect_to_login


# Define the role hierarchy.
# A role inherits all the permissions of the roles listed below it.
ROLE_HIERARCHY = {
    'Enseignant': ['Enseignant'],
    'Concepteur': ['Concepteur', 'Enseignant'],
    'Référent': ['Référent', 'Concepteur', 'Enseignant'],
    'Superviseur': ['Superviseur', 'Référent', 'Concepteur', 'Enseignant'],
    'Administrateur': ['Administrateur', 'Superviseur', 'Référent', 'Concepteur', 'Enseignant'],
}


def get_user_roles(user):
    """
    Returns a set of all roles the user has, including inherited ones.
    """
    if not user.is_authenticated:
        return set()
    
    # Superusers and Administrators have all roles
    if user.is_superuser or user.groups.filter(name='Administrateur').exists():
        return set(ROLE_HIERARCHY['Administrateur'])
        
    user_groups = set(user.groups.values_list('name', flat=True))
    all_roles = set()
    
    for group in user_groups:
        if group in ROLE_HIERARCHY:
            all_roles.update(ROLE_HIERARCHY[group])
        else:
            all_roles.add(group)
            
    return all_roles


def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has a specific role,
    taking role hierarchy into account.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            
            user_roles = get_user_roles(request.user)
            
            # If the user has at least one of the allowed roles (direct or inherited)
            if any(role in user_roles for role in allowed_roles):
                return view_func(request, *args, **kwargs)
                
            raise PermissionDenied
        return _wrapped_view
    return decorator


# --- Shorthand Decorators for easier reading ---
# Usage: @is_teacher, @is_designer, etc.
is_teacher = role_required(['Enseignant'])
is_designer = role_required(['Concepteur'])
is_referee = role_required(['Référent'])
is_supervisor = role_required(['Superviseur'])