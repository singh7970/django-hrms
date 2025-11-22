from django.db import models
from django.conf import settings
from .role import Role

class UserRole(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'user_role'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'


    def __str__(self):
        return f"{self.user.email} → {self.role.name}"
