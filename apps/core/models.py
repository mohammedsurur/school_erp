from django.db import models

class School(models.Model):
    """One record per school — extendable for multi-school"""
    name         = models.CharField(max_length=200)
    logo         = models.ImageField(upload_to='school/', blank=True)
    address      = models.TextField()
    phone        = models.CharField(max_length=20)
    email        = models.EmailField()
    website      = models.URLField(blank=True)
    motto        = models.CharField(max_length=200, blank=True)
    established  = models.DateField(blank=True, null=True)

    def __str__(self): return self.name

class AcademicYear(models.Model):
    name       = models.CharField(max_length=20)  # e.g. "2024-2025"
    start_date = models.DateField()
    end_date   = models.DateField()
    is_current = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self): return self.name

class Term(models.Model):
    TERM_CHOICES = [('1','Semister 1'),('2','Semister 2'),]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='terms')
    name          = models.CharField(max_length=10, choices=TERM_CHOICES)
    start_date    = models.DateField()
    end_date      = models.DateField()
    is_current    = models.BooleanField(default=False)

    def __str__(self): return f"{self.academic_year} — Term {self.name}"

class AuditLog(models.Model):
    """Tracks every important action in the system"""
    user       = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    action     = models.CharField(max_length=50)   # CREATE, UPDATE, DELETE
    model_name = models.CharField(max_length=100)
    object_id  = models.CharField(max_length=50)
    detail     = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp  = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ['-timestamp']