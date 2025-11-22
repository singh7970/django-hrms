from django.db import models

class LeaveTypes(models.Model):

    class Meta:
        db_table = 'leave_types'

    name = models.CharField(max_length=50, unique=True)
    code=  models.CharField(max_length=10, unique=True) # E.g., Casual Leave, Sick Leave, etc.
    days = models.FloatField(default=0.0)
    # Common fields for tracking changes
    row_create_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=True)  # If false, leave type is disabled

    def __str__(self):
        return self.name
