from django.db import models
from django.core.exceptions import ValidationError
from hrms_app.models import UserProfile, user_role

class UserGroup(models.Model):
    emp_user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='employee_groups'
    )
    authority_user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='authority_users'
    )
    class Meta:
        db_table = 'user_groups'
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True, blank=True)
