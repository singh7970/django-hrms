from django.db import models
from hrms_app.models import UserProfile  # Adjust the path if needed

class JobDetails(models.Model):
    EMPLOYMENT_STATUS_CHOICES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    ]

    class Meta:
        db_table = 'job_details'

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='job_details')

  
    job_title = models.CharField(max_length=100)
    job_category = models.CharField(max_length=100)
    sub_unit = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    job_specification = models.CharField(max_length=255, blank=True, null=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES)

    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.job_title}"
