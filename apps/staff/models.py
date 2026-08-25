
from django.db import models


class Staff(models.Model):

    STAFF_TYPE = [
        ('teaching',     'Teaching'),
        ('non_teaching', 'Non-Teaching'),
        ('admin',        'Administration'),
    ]
    QUALIFICATION = [
        ('diploma',  'Diploma'),
        ('degree',   'Degree'),
        ('masters',  'Masters'),
        ('phd',      'PhD'),
    ]

    user                    = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    staff_id                = models.CharField(max_length=20, unique=True)
    staff_type              = models.CharField(max_length=20, choices=STAFF_TYPE)
    department              = models.CharField(max_length=100, blank=True)
    qualification           = models.CharField(max_length=20, choices=QUALIFICATION)
    specialization          = models.CharField(max_length=100, blank=True)
    experience_years        = models.PositiveIntegerField(default=0)
    join_date               = models.DateField()
    salary                  = models.DecimalField(max_digits=10, decimal_places=2)
    bank_name               = models.CharField(max_length=100, blank=True)
    bank_account            = models.CharField(max_length=50, blank=True)
    emergency_contact_name  = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    is_active               = models.BooleanField(default=True)
    photo                   = models.ImageField(upload_to='staff/', blank=True, null=True)

    class Meta:
        verbose_name        = 'Staff'
        verbose_name_plural = 'Staff'
        ordering            = ['-join_date']

    def __str__(self):
        return f"{self.staff_id} — {self.user.get_full_name()}"

    # ── Auto generate staff ID ────────────────
    @classmethod
    def generate_staff_id(cls):
        from datetime import date
        year  = date.today().year
        count = cls.objects.filter(
            staff_id__startswith=f'STF{year}'
        ).count()
        return f"STF{year}{str(count + 1).zfill(4)}"
        # e.g. STF20240001, STF20240002 ...