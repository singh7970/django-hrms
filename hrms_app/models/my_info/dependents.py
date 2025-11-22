from django.db import models
from hrms_app.models import UserProfile

class Dependent(models.Model):
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('other', 'Other'),
    ]
    class Meta:
            db_table = 'dependent'

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='dependents')
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    dob = models.DateField()

    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.relationship} - {self.user.username}"
