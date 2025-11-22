from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import UserProfile, JobDetails, UserRole
from django.core.paginator import Paginator


@login_required
def employee_directory_view(request):
    return render(request, 'directory.html')


@login_required
def get_all_employees(request):
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 5)  

    employees_queryset = UserProfile.objects.select_related('job_details').filter(
        job_details__isnull=False
    ).order_by('first_name', 'last_name')

    paginator = Paginator(employees_queryset, page_size)
    page_obj = paginator.get_page(page_number)

    data = []
    for emp in page_obj:
        job = emp.job_details
        full_name = f"{emp.first_name} {emp.last_name}".strip() or emp.username

        data.append({
            'id': emp.id,
            'name': full_name,
            'email': emp.email,
            'job_title': job.job_title or 'N/A',
            'job_category': job.job_category or 'N/A',
            'location': job.location or 'N/A',
            'sub_unit': job.sub_unit or 'N/A',
            'employment_status': job.get_employment_status_display() if job.employment_status else 'N/A',
            # 'joined_date': job.joined_date.strftime('%Y-%m-%d') if job.joined_date else '',
            'job_specification': job.job_specification or 'N/A',
        })

    return JsonResponse({
        'success': True,
        'employees': data,
        'total_pages': paginator.num_pages,
        'total_records': paginator.count,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous()
    })


@login_required
def search_employees(request):
    name = request.GET.get('name', '')
    job_title = request.GET.get('job_title', '')
    location = request.GET.get('location', '')
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 5)

    query = UserProfile.objects.select_related('job_details').filter(job_details__isnull=False)

    if name:
        query = query.filter(Q(first_name__icontains=name) | Q(last_name__icontains=name) |
                             Q(username__icontains=name) | Q(email__icontains=name))

    if job_title:
        query = query.filter(job_details__job_title__icontains=job_title)

    if location:
        query = query.filter(job_details__location__icontains=location)

    employees_queryset = query.order_by('first_name', 'last_name')
    paginator = Paginator(employees_queryset, page_size)
    page_obj = paginator.get_page(page_number)

    data = []
    for emp in page_obj:
        job = emp.job_details
        full_name = f"{emp.first_name} {emp.last_name}".strip() or emp.username

        data.append({
            'id': emp.id,
            'name': full_name,
            'email': emp.email,
            'job_title': job.job_title or 'N/A',
            'job_category': job.job_category or 'N/A',
            'location': job.location or 'N/A',
            'sub_unit': job.sub_unit or 'N/A',
            'employment_status': job.get_employment_status_display() if job.employment_status else 'N/A',
            # 'joined_date': job.joined_date.strftime('%Y-%m-%d') if job.joined_date else '',
            'job_specification': job.job_specification or 'N/A',
        })

    return JsonResponse({
        'success': True,
        'employees': data,
        'total_pages': paginator.num_pages,
        'total_records': paginator.count,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous()
    })


@login_required
def get_dropdown_options(request):
    job_titles = list(JobDetails.objects.exclude(job_title='').values_list('job_title', flat=True).distinct())
    locations = list(JobDetails.objects.exclude(location='').values_list('location', flat=True).distinct())

    return JsonResponse({
        'success': True,
        'job_titles': job_titles,
        'locations': locations
    })