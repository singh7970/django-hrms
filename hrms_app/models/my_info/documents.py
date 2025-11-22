from django.db import models

from hrms_app.models import UserProfile


class PersonalDocument(models.Model):
    DOCUMENT_CHOICES = [

        ('aadhaar', 'Aadhaar'),
        ('pan', 'PAN Card'),
        ('passport', 'Passport'),
        ('voter', 'Voter ID'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_CHOICES)
    document_file = models.FileField(upload_to='personal_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = [('user', 'document_type')]  # restrict one type per user (especially for profile_photo)

    def __str__(self):
        return f"{self.user.username} - {self.document_type}"
