from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime
import logging

from hrms_app.models.performance.emp_review_details import EmployeeReview
from hrms_app.models.performance.user_group import UserGroup
from hrms_app.models.users import UserProfile
from hrms_app.models.my_info.job_details import JobDetails

logger = logging.getLogger(__name__)

@login_required(login_url='/hrms_app/login/')
def employee_reviews(request):
    user = request.user
    user_role = getattr(user, 'userrolepermission', None)
    role_name = user_role.role.name if user_role else 'employee'

    # ✅ Handle AJAX request for job_title and sub_unit autofill
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.GET.get('employee_name'):
        emp_id = request.GET.get('employee_name')
        try:
            user_obj = UserProfile.objects.get(id=emp_id)
            job = JobDetails.objects.get(user=user_obj)
            return JsonResponse({
                'job_title': job.job_title,
                'sub_unit': job.sub_unit
            })
        except (UserProfile.DoesNotExist, JobDetails.DoesNotExist) as e:
            logger.warning(f"JobDetails fetch failed: {e}")
            return JsonResponse({
                'job_title': '',
                'sub_unit': '',
                'error': 'Job details not found'
            })

    # 🔎 Employees under this manager's authority
    employee_ids = UserGroup.objects.filter(authority_user=user).values_list('emp_user_id', flat=True)
    employees = UserProfile.objects.filter(id__in=employee_ids)

    # Get filter inputs
    employee_id = request.GET.get('employee_name', '').strip()
    job_title = request.GET.get('job_title', '').strip()
    sub_unit = request.GET.get('sub_unit', '').strip()
    include = request.GET.get('include', '').strip()
    review_status = request.GET.get('review_status', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    review_type = request.GET.get('review_type', '').strip()

    reviews = EmployeeReview.objects.none()

    if any([employee_id, job_title, sub_unit, include, review_status, review_type, from_date, to_date]):
        reviews = EmployeeReview.objects.all()

        if employee_id:
            reviews = reviews.filter(user__id=employee_id)
            # Try to auto-fill job title and sub unit if not provided
            if not job_title or not sub_unit:
                try:
                    emp = UserProfile.objects.get(id=employee_id)
                    job = JobDetails.objects.get(user=emp)
                    if not job_title:
                        job_title = job.job_title
                    if not sub_unit:
                        sub_unit = job.sub_unit
                except Exception as e:
                    logger.warning(f"Auto-fill job/sub_unit failed: {e}")

        if job_title:
            user_ids = JobDetails.objects.filter(job_title__icontains=job_title).values_list('user_id', flat=True)
            reviews = reviews.filter(user__id__in=user_ids)

        if sub_unit:
            user_ids = JobDetails.objects.filter(sub_unit__icontains=sub_unit).values_list('user_id', flat=True)
            reviews = reviews.filter(user__id__in=user_ids)
        if include:
            reviews = reviews.filter(include__icontains=include)

        if review_status:
            reviews = reviews.filter(review_status__icontains=review_status)

        if review_type:
            reviews = reviews.filter(review_type__icontains=review_type)

        if from_date and to_date:
            try:
                from_parsed = datetime.strptime(from_date, '%Y-%m-%d').date()
                to_parsed = datetime.strptime(to_date, '%Y-%m-%d').date()
                reviews = reviews.filter(review_date__range=(from_parsed, to_parsed))
            except Exception as e:
                logger.error(f"Date parsing error: {e}")

    context = {
        'reviews': reviews,
        'user_role': role_name,
        'form_data': {
            'employee_name': employee_id,
            'job_title': job_title,
            'sub_unit': sub_unit,
            'include': include,
            'review_status': review_status,
            'from_date': from_date,
            'to_date': to_date,
            'review_type': review_type,
        },
        'employees': employees,
    }

    return render(request, "performance/employee_review.html", context)
