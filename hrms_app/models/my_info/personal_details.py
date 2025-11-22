from django.db import models
from hrms_app.models import UserProfile

class PersonalDetails(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]

    NATIONALITY_CHOICES = [
        ('indian', 'Indian'),
        ('american', 'American'),
        ('canadian', 'Canadian'),
        ('british', 'British'),
    ]

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='personal_info')
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    other_id = models.CharField(max_length=50, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    license_expiry = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=20, choices=NATIONALITY_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = 'personal_details'

    def __str__(self):
        return f"{self.user.email} - Personal Info"
