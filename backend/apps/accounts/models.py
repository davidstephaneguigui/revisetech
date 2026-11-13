from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User Model.
    We use AbstractUser to keep all the default Django features 
    (username, password, email, first_name, last_name, etc.)
    Roles (Student, Teacher, Designer, etc.) will be handled later 
    using Django's native Group and Permission system.
    """
    # You can add custom fields here later (e.g., student_id, phone_number)
    
    def __str__(self):
        return self.username