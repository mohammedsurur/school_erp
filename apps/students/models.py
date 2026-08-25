from django.db import models

# Create your models here.
class Student(models.Model):
    GENDER = [('M','Male'),('F','Female')]
    BLOOD  = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
              ('O+','O+'),('O-','O-'),('AB+','AB+'),('AB-','AB-')]

    user              = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    admission_number  = models.CharField(max_length=20, unique=True)
    roll_number       = models.CharField(max_length=20, blank=True)
    date_of_birth     = models.DateField()
    gender            = models.CharField(max_length=1, choices=GENDER)
    blood_group       = models.CharField(max_length=3, choices=BLOOD, blank=True)
    nationality       = models.CharField(max_length=50, blank=True)
    religion          = models.CharField(max_length=50, blank=True)
    address           = models.TextField()
    city              = models.CharField(max_length=100, blank=True)
    admission_date    = models.DateField(auto_now_add=True)
    previous_school   = models.CharField(max_length=200, blank=True)
    medical_notes     = models.TextField(blank=True)
    photo             = models.ImageField(upload_to='students/', blank=True, null=True)
    is_active         = models.BooleanField(default=True)

    def __str__(self): return f"{self.admission_number} — {self.user.get_full_name()}"

    @classmethod
    def generate_admission_number(cls):
        from datetime import date
        year = date.today().year
        last = cls.objects.filter(admission_number__startswith=str(year)).count()
        return f"{year}{str(last+1).zfill(4)}"

class Parent(models.Model):
    RELATION = [('father','Father'),('mother','Mother'),('guardian','Guardian')]
    user       = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    student    = models.ManyToManyField(Student, related_name='parents')
    relation   = models.CharField(max_length=20, choices=RELATION)
    occupation = models.CharField(max_length=100, blank=True)
    work_phone = models.CharField(max_length=20, blank=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

class Enrollment(models.Model):
    student       = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    section       = models.ForeignKey('academic.Section', on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey('core.AcademicYear', on_delete=models.CASCADE)
    enrolled_date = models.DateField(auto_now_add=True)
    is_active     = models.BooleanField(default=True)
    is_promoted   = models.BooleanField(default=False)

    class Meta: unique_together = ['student', 'academic_year']