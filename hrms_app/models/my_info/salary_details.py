from django.db import models
from hrms_app.models import UserProfile  # replace 'your_app' with actual app name


class Salary(models.Model):
    PAYMENT_MODES = [
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='salaries')

    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    hra = models.DecimalField("House Rent Allowance", max_digits=10, decimal_places=2)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES, default='bank_transfer')

    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = 'salary_details'

    def __str__(self):
        return f"{self.user.email} - {self.net_salary}"
