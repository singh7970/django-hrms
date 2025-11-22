from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from hrms_app.models.my_info.job_details import JobDetails
from hrms_app.models.my_info.contact_details import ContactDetails
from hrms_app.models.my_info.personal_details import PersonalDetails
from hrms_app.models.my_info.salary_details import Salary
from hrms_app.models.user_leave_mapping import UserLeaveMapping
from hrms_app.models.time_attendance_record import AttendanceRecord
from django.db.models import Sum
from datetime import datetime, timedelta


@login_required(login_url='/hrms_app/login/')
def show_dashboard_page(request):
    user_profile = request.user  

    job_details = JobDetails.objects.filter(user=user_profile).first()
    contact_details = ContactDetails.objects.filter(user=user_profile).first()
    personal_details = PersonalDetails.objects.filter(user=user_profile).first()
    salary = Salary.objects.filter(user=user_profile).first()
    user_leaves = UserLeaveMapping.objects.filter(user_profile=request.user)

    total_remaining_leaves = user_leaves.aggregate(total=Sum('remaining_leaves'))['total'] or 0

    latest_attendance = AttendanceRecord.objects.filter(user=user_profile).order_by('-punch_in_time').first()
    
    # Calculate today's total working time
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = today_start + timedelta(days=1)
    
    # Get all attendance records for today
    today_attendance = AttendanceRecord.objects.filter(
        user=user_profile,
        punch_in_time__gte=today_start,
        punch_in_time__lt=today_end
    )
    
    # Calculate total seconds worked today
    total_seconds_today = 0
    current_session_duration = 0
    
    for record in today_attendance:
        if record.duration and record.status == 'PUNCHED_OUT':
            # Completed sessions
            total_seconds_today += record.duration
        elif record.status == 'PUNCHED_IN' and record.punch_out_time is None:
            # Current active session
            current_session_duration = (datetime.now() - record.punch_in_time).total_seconds()
    
    # Add current session duration to total
    total_seconds_today += current_session_duration
    
    # Convert to H:M:S format
    hours = int(total_seconds_today // 3600)
    minutes = int((total_seconds_today % 3600) // 60)
    seconds = int(total_seconds_today % 60)
    total_hours_today = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    # If no records for today, show 00:00:00
    if total_seconds_today == 0:
        total_hours_today = "00:00:00"
    
    # Calculate working days this month (only days with punch in/out)
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get all attendance records for current month
    month_start = datetime(current_year, current_month, 1)
    if current_month == 12:
        month_end = datetime(current_year + 1, 1, 1)
    else:
        month_end = datetime(current_year, current_month + 1, 1)
    
    # Get unique days with completed attendance records (punch in AND punch out)
    working_days_this_month = AttendanceRecord.objects.filter(
        user=user_profile,
        punch_in_time__gte=month_start,
        punch_in_time__lt=month_end,
        punch_out_time__isnull=False,  # Only count days with punch out (completed sessions)
        status='PUNCHED_OUT'  # Only count completed sessions
    ).dates('punch_in_time', 'day').distinct().count()
    
    # Check if user is currently punched in
    is_punched_in = latest_attendance and latest_attendance.status == 'PUNCHED_IN' and latest_attendance.punch_out_time is None

    context = {
        'user': user_profile,
        'job_details': job_details,
        'contact_details': contact_details,
        'latest_attendance': latest_attendance,
        'user_leaves': user_leaves,
        'total_remaining_leaves': total_remaining_leaves,
        'total_hours_today': total_hours_today,
        'is_punched_in': is_punched_in,
        'working_days_this_month': working_days_this_month,
    }
    return render(request, 'dashboard.html', context)
