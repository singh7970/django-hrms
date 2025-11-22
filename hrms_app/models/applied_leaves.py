from django.db import models
from .leave_types import LeaveTypes
from .users import UserProfile
from django.utils.timezone import now
from django.contrib.auth import authenticate

class AppliedLeaves(models.Model):

    class Meta:
        db_table = 'applied_leaves'

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveTypes, on_delete=models.CASCADE)
    leave_date = models.DateField() 
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Cancelled','Cancelled')],
        default='Pending'
    )
    DURATION_CHOICES = [
        ('full', 'Full Day'),
        ('half_morning', 'Half Day - Morning'),
        ('half_evening', 'Half Day - Evening'),
    ]
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES, default='full')
    

    # Common fields for tracking changes
    row_create_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user_profile.username} - {self.leave_type.name} ({self.leave_date}) ({self.duration})({self.status})"
# class AppliedLeaveDates(models.Model):
#     applied_leave = models.ForeignKey(AppliedLeaves, on_delete=models.CASCADE, related_name="leave_dates")
#     leave_date = models.DateField()
#     duration = models.CharField(
#         max_length=20,
#         choices=[
#             ('full', 'Full Day'),
#             ('half_morning', 'Half Day - Morning'),
#             ('half_evening', 'Half Day - Evening'),
#         ],
#         default='full'
#     )

#     def __str__(self):
#         return f"{self.leave_date} ({self.duration})"