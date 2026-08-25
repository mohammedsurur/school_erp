# apps/students/api_views.py
from rest_framework import viewsets, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import *
from .serializers import *
class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.filter(is_active=True)
    serializer_class = StudentSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['gender', 'enrollments__section__grade']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name']