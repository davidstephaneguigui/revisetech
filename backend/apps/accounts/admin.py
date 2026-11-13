from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# We register our custom User model using Django's built-in UserAdmin
# to keep the password hashing and permissions features working.
admin.site.register(User, UserAdmin)