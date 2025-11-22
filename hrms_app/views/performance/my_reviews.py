from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from hrms_app.models.performance.emp_review_details import EmployeeReview
from hrms_app.models.my_info.job_details import JobDetails

@login_required
def my_reviews(request):
    current_user = request.user

    # Get all reviews for the logged-in employee
    reviews = EmployeeReview.objects.filter(user=current_user)

    # Get job details for the employee
    job_details = JobDetails.objects.filter(user=current_user).first()

    context = {
        "reviews": reviews,
        "job_title": job_details.job_title if job_details else "N/A",
        "sub_unit": job_details.sub_unit if job_details else "N/A",
    }

    return render(request, 'performance/my_reviews.html', context)



from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from hrms_app.models.performance.emp_review_details import EmployeeReview

@login_required
def review_detail_view(request, review_id):
    review = get_object_or_404(EmployeeReview, id=review_id, user=request.user)

    data = {
        'employee_name': review.employee_name,
        'job_title': review.job_title,
        'sub_unit': review.sub_unit,
        'review_date': review.review_date.strftime('%Y-%m-%d') if review.review_date else '',
        'comments': review.comments or '-',
        
    }
    return JsonResponse(data)
