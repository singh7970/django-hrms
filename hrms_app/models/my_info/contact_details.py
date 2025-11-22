from django.db import models
from django.conf import settings
from hrms_app.models import UserProfile

class ContactDetails(models.Model):

    class Meta:
        db_table = 'contact_details'

    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE,  related_name='contact_details')
    street_1 = models.CharField(max_length=255)
    street_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    home_phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20)
    work_phone = models.CharField(max_length=20, blank=True)
    work_email = models.EmailField()
    other_email = models.EmailField(blank=True)
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50 ,default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Contact Details of {self.user.username}"
