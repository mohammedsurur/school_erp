from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ('super_admin',  'Super Admin'),
        ('principal',    'Principal'),
        ('admin_staff',  'Admin Staff'),
        ('teacher',      'Teacher'),
        ('student',      'Student'),
        ('parent',       'Parent'),
        ('librarian',    'Librarian'),
        ('accountant',   'Accountant'),
    ]

    role          = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone         = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    address       = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender        = models.CharField(max_length=10, choices=[
                        ('male','Male'),('female','Female'),('other','Other')
                    ], blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name       = 'User'
        verbose_name_plural = 'Users'
        ordering            = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    # ── Role helpers ───────────────────────────
    def is_super_admin(self):  return self.role == 'super_admin'
    def is_principal(self):    return self.role == 'principal'
    def is_admin_staff(self):  return self.role == 'admin_staff'
    def is_teacher(self):      return self.role == 'teacher'
    def is_student(self):      return self.role == 'student'
    def is_parent(self):       return self.role == 'parent'
    def is_librarian(self):    return self.role == 'librarian'
    def is_accountant(self):   return self.role == 'accountant'

    def is_school_admin(self):
        return self.role in ['super_admin', 'principal', 'admin_staff']

    def get_dashboard_url(self):
        urls = {
            'super_admin': '/dashboard/admin/',
            'principal':   '/dashboard/principal/',
            'admin_staff': '/dashboard/admin/',
            'teacher':     '/dashboard/teacher/',
            'student':     '/dashboard/student/',
            'parent':      '/dashboard/parent/',
            'librarian':   '/dashboard/librarian/',
            'accountant':  '/dashboard/accountant/',
        }
        return urls.get(self.role, '/dashboard/')