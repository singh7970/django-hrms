from django.db import models
from django.conf import settings
from hrms_app.models.users import UserProfile


class AttendanceRecord(models.Model):
    class Meta:
        db_table = 'attendance_record'

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='attendances')
    punch_in_time = models.DateTimeField()
    punch_out_time = models.DateTimeField(null=True, blank=True)
    punch_in_note = models.TextField(blank=True, null=True)
    punch_out_note = models.TextField(blank=True, null=True)    
    duration = models.FloatField(blank=True, null=True )   
    status_choices = (
        ('PUNCHED_IN', 'Punched In'),
        ('PUNCHED_OUT', 'Punched Out'),
    )
    status = models.CharField(max_length=20, choices=status_choices, default='PUNCHED_IN')
    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, null=True,blank=True)

    def duration_hms(self):
        if self.duration is not None:
            total_seconds = int(self.duration)
            milliseconds = int((self.duration - total_seconds) * 1000)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        return "00:00:00.00"
    
    def is_half_day(self):
        """Check if this attendance record is a half day (4 hours)"""
        if self.duration is not None:
            hours = self.duration / 3600  # Convert seconds to hours
            return hours >= 4 and hours < 8
        return False
    
    def is_full_day(self):
        """Check if this attendance record is a full day (8+ hours)"""
        if self.duration is not None:
            hours = self.duration / 3600  # Convert seconds to hours
            return hours >= 8
        return False

    def save(self, *args, **kwargs):
        if self.punch_in_time and self.punch_out_time:
            delta = self.punch_out_time - self.punch_in_time
            self.duration = round(delta.total_seconds(), 2)  # Store as float
            self.status = 'PUNCHED_OUT'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.punch_in_time.strftime('%Y-%m-%d %H:%M')}"
