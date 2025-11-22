from django.db import models
from hrms_app.models import UserProfile

class Immigration(models.Model):
    DOCUMENT_CHOICES = [
        ('visa', 'Visa'),
        ('passport', 'Passport'),
    ]

    COUNTRY_CHOICES = [
        ('india', 'India'),
        ('united_states', 'United States'),
        ('china', 'China'),
        ('russia', 'Russia'),
        ('germany', 'Germany'),
        ('japan', 'Japan'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='immigration_records')

    document_type = models.CharField(max_length=20, choices=DOCUMENT_CHOICES)
    number = models.CharField(max_length=100)
    issued_date = models.DateField()
    expiry_date = models.DateField()
    eligible_state = models.CharField(max_length=100)
    issued_by = models.CharField(max_length=50, choices=COUNTRY_CHOICES)
    eligible_review_date = models.DateField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'immigration_details'

    def __str__(self):
        return f"{self.document_type.title()} - {self.user.username}"
    