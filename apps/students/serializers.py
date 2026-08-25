# apps/students/serializers.py
from rest_framework import serializers
from .models import *
class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id','admission_number','full_name','date_of_birth',
                  'gender','photo','is_active']

    def get_full_name(self, obj):
        return obj.user.get_full_name()

