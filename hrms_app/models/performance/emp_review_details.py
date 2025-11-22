from django.db import models
from django.conf import settings
from hrms_app.models import UserProfile
from hrms_app.models.my_info.job_details import JobDetails

class EmployeeReview(models.Model):
    class Meta:
        db_table = 'employees_reviews'

    # One user (employee) can have many reviews
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )

    review_date = models.DateField(auto_now_add=True)

    comments = models.TextField(blank=True, null=True)

    # Who created the review
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_created'
    )

    row_created_date = models.DateTimeField(auto_now_add=True)
    row_modified_date = models.DateTimeField(auto_now=True)
    row_created_by = models.CharField(max_length=50, default='sysusr')
    row_modified_by = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.review_date} Review"

    @property
    def job_title(self):
        job = JobDetails.objects.filter(user=self.user).first()
        return job.job_title if job else 'N/A'

    @property
    def sub_unit(self):
        job = JobDetails.objects.filter(user=self.user).first()
        return job.sub_unit if job else 'N/A'

    @property
    def employee_name(self):
        return self.user.get_full_name()
