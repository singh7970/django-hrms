from django.db import models

class Holiday(models.Model):
    class Meta:
        db_table = 'Holiday_dates'
    date = models.DateField(unique=True)
    occasion = models.CharField(max_length=255)

    row_create_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=True)  # If false, leave type is disabled



    def __str__(self):
        return f"{self.occasion} on {self.date}"