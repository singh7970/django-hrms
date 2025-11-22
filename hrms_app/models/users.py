from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

class UserProfile(AbstractUser):

    class Meta:
        db_table = 'user_profile'
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    email = models.EmailField(unique=True)
    dob = models.DateField(default=date(2000, 1, 1)) 
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['username']  

    def __str__(self):
        return self.email