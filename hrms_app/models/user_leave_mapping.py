import datetime
from django.db import models
from .leave_types import LeaveTypes
from .users import UserProfile
from django.utils.timezone import now

class UserLeaveMapping(models.Model):

    class Meta:
        db_table = 'user_leave_mapping'

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveTypes, on_delete=models.CASCADE)
    total_leaves = models.FloatField(default=0.0)
    used_leaves = models.FloatField(default=0.0)
    remaining_leaves = models.FloatField(default=0.0)
    year = models.IntegerField(default=now().year)
    is_active = models.BooleanField(default=True)

    row_create_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True)

    def save(self, *args, **kwargs):
        """ Auto-disable old year's records and activate new ones """
        current_year = now().year
        if self.year < current_year:
            self.is_active = False
        elif self.year == current_year:
            self.is_active = True

        self.remaining_leaves = self.total_leaves - self.used_leaves

        # Do not try to fetch leave_balance here with request.user — remove it.
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_profile.username} - {self.leave_type.name} ({self.remaining_leaves} left in {self.year})"
