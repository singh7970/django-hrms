from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from hrms_app.models.my_info.job_details import JobDetails


@login_required(login_url='/hrms_app/login/')
def job_details_page(request):
    user_profile = request.user

    job_details = JobDetails.objects.filter(user=user_profile).first()

    # Hardcoded job titles list
    job_titles = [
        "Software Engineer", "Frontend Developer", "Backend Developer", "DevOps Engineer",
        "System Administrator", "Data Analyst", "QA Engineer", "Project Manager",
        "Product Manager", "Operations Manager", "HR Manager", "Team Lead",
        "Business Analyst", "Marketing Executive", "Sales Associate", "Customer Support",
        "Office Administrator", "Accountant", "Financial Analyst", "Legal Advisor",
        "Compliance Officer", "HR Executive", "Recruiter", "Training Manager",
        "Learning & Development Specialist"
    ]
    sub_units = [
    "Engineering", "Human Resources", "Marketing", "Sales", "Operations",
    "Finance", "Customer Support", "Product", "Legal", "IT", "Administration"
]

    if request.method == "POST":
        joined_date = request.POST.get('joined_date')
        job_title = request.POST.get('job_title')
        job_category = request.POST.get('job_category')
        sub_unit = request.POST.get('sub_unit')
        location = request.POST.get('location')
        job_specification = request.POST.get('job_specification')
        employment_status = request.POST.get('employment_status')

        if job_details:
            
            job_details.job_title = job_title
            job_details.job_category = job_category
            job_details.sub_unit = sub_unit
            job_details.location = location
            job_details.job_specification = job_specification
            job_details.employment_status = employment_status
            job_details.row_modified_by = request.user.username
            job_details.save()
        else:
            JobDetails.objects.create(
                user=user_profile,
                
                job_title=job_title,
                job_category=job_category,
                sub_unit=sub_unit,
                location=location,
                job_specification=job_specification,
                employment_status=employment_status,
                row_created_by=request.user.username
            )

        return redirect('job_details_page')

    return render(request, 'my_info/job_details.html', {
    'job_details': job_details,
    'job_titles': job_titles,
    'sub_units': sub_units
})
