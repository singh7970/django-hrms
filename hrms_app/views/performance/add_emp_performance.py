from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse

from hrms_app.models.performance.emp_review_details import EmployeeReview
from hrms_app.models.user_role import UserRole
from hrms_app.models.performance.user_group import UserGroup
from hrms_app.models.users import UserProfile
from hrms_app.models.my_info.job_details import JobDetails
from django.shortcuts import get_object_or_404


@login_required(login_url='/hrms_app/login/')
def add_employee_reviews(request):
    try:
        user_role = UserRole.objects.get(user=request.user)
        if user_role.role.name != 'manager':
            return redirect('my_reviews')  # Redirect non-managers
    except UserRole.DoesNotExist:
        return redirect('my_reviews')  # No role = no access

    # ✅ Get employees under this manager's authority
    employee_ids = UserGroup.objects.filter(authority_user=request.user).values_list('emp_user_id', flat=True)
    employees = UserProfile.objects.filter(id__in=employee_ids)

    if request.method == "POST":
        employee_id = request.POST.get("employee_name")
        comments = request.POST.get("comments")

        employee = get_object_or_404(UserProfile, id=employee_id)

        # Save only what exists in EmployeeReview
        EmployeeReview.objects.create(
            user=employee,
            comments=comments,
            created_by=request.user
        )

       
        return redirect('add_employee_reviews')

    return render(request, "performance/add_employee_performance.html", {
        'employees': employees
    })

@login_required(login_url='/hrms_app/login/')
def get_job_details(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user_id = request.GET.get('user_id')
   

    try:
        user = UserProfile.objects.get(id=user_id)
        job = JobDetails.objects.get(user=user)

        

        data = {
            'job_title': job.job_title,
            'sub_unit': job.sub_unit
        }

    except (UserProfile.DoesNotExist, JobDetails.DoesNotExist) as e:
       
        data = {
            'job_title': None,
            'sub_unit': None
        }

    return JsonResponse(data)
