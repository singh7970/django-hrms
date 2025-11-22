from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime, date, timedelta
from hrms_app.models.time_attendance_record import AttendanceRecord
from hrms_app.models.users import UserProfile
from hrms_app.constants import WORK_DAY_END_TIME, MAX_WORK_HOURS
# Remove this line temporarily:
# from hrms_app.utils import parse_iso_datetime
import json
import logging

logger = logging.getLogger(__name__)


@login_required(login_url='/hrms_app/login/')
def hr_attendance_dashboard(request):
    """Main HR attendance management dashboard"""
    
    # Get date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    name_search = request.GET.get('name_search')
    employee_filter = request.GET.get('employee')
    status_filter = request.GET.get('status')
    
    # Default to current month if no dates specified
    if not start_date:
        start_date = (date.today().replace(day=1)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    # Base queryset
    records = AttendanceRecord.objects.all()
    
    # Apply filters
    if start_date:
        parsed_start_date = parse_date(start_date)
        if parsed_start_date:
            start_datetime = datetime.combine(parsed_start_date, datetime.min.time())
            records = records.filter(punch_in_time__gte=start_datetime)
        else:
            # Handle invalid date format
            messages.warning(request, f"Invalid start date format: {start_date}")
    
    if end_date:
        parsed_end_date = parse_date(end_date)
        if parsed_end_date:
            end_datetime = datetime.combine(parsed_end_date, datetime.max.time())
            records = records.filter(punch_in_time__lte=end_datetime)
    
    if name_search:
        records = records.filter(user__username__icontains=name_search)
    
    if employee_filter:
        records = records.filter(user__username__icontains=employee_filter)
    
    if status_filter:
        records = records.filter(status=status_filter)
    
    # Order by most recent first
    records = records.order_by('-punch_in_time')
    
    # Pagination
    paginator = Paginator(records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_employees = UserProfile.objects.filter(is_active=True).count()
    
    # Today's statistics
    today = date.today()
    today_records = AttendanceRecord.objects.filter(
        punch_in_time__date=today
    )
    present_today = today_records.filter(status='PUNCHED_IN').count()
    absent_today = total_employees - present_today
    
    # Early departures (before work day end time)
    early_departures = today_records.filter(
        punch_out_time__time__lt=datetime.strptime(WORK_DAY_END_TIME, '%H:%M').time()
    ).count()
    
    # Employees currently punched in (haven't punched out)
    currently_punched_in = today_records.filter(
        status='PUNCHED_IN',
        punch_out_time__isnull=True
    ).count()
    
    # Employees punched in for over maximum work hours (critical warning)
    from datetime import timedelta
    max_hours_ago = timezone.now() - timedelta(hours=MAX_WORK_HOURS)
    over_max_hours_records = AttendanceRecord.objects.filter(
        status='PUNCHED_IN',
        punch_out_time__isnull=True,
        punch_in_time__lt=max_hours_ago
    ).select_related('user').order_by('punch_in_time')
    over_max_hours_count = over_max_hours_records.count()
    
    # Get all employees for filter dropdown
    employees = UserProfile.objects.filter(is_active=True).order_by('username')
    
    context = {
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'name_search': name_search,
        'employee_filter': employee_filter,
        'status_filter': status_filter,
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'early_departures': early_departures,
        'currently_punched_in': currently_punched_in,
        'over_40_hours_count': over_max_hours_count,
        'over_40_hours_records': over_max_hours_records,
        'employees': employees,
        'today': today.isoformat(),
    }
    
    return render(request, 'hr_dashboard/hr_attendance_management.html', context)

@login_required(login_url='/hrms_app/login/')

def edit_attendance_record(request, record_id):
    """Edit an attendance record"""
    if request.method == 'POST':
        record = get_object_or_404(AttendanceRecord, id=record_id)
        
        try:
            data = json.loads(request.body)
            punch_in_time = data.get('punch_in_time')
            punch_out_time = data.get('punch_out_time')
            punch_in_note = data.get('punch_in_note', '')
            punch_out_note = data.get('punch_out_note', '')
            
            if punch_in_time:
                record.punch_in_time = datetime.fromisoformat(punch_in_time.replace('Z', '+00:00'))
            if punch_out_time:
                record.punch_out_time = datetime.fromisoformat(punch_out_time.replace('Z', '+00:00'))
            
            record.punch_in_note = punch_in_note
            record.punch_out_note = punch_out_note
            record.row_modified_by = request.user.username
            record.save()
            
            return JsonResponse({'success': True, 'message': 'Record updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required(login_url='/hrms_app/login/')

def delete_attendance_record(request, record_id):
    """Delete an attendance record"""
    if request.method == 'POST':
        try:
            record = get_object_or_404(AttendanceRecord, id=record_id)
            
            # Check if user has permission to delete this record
            # (Optional: Add role-based checks here)
            
            # Store record info for logging/debugging
            record_info = f"Record {record_id} for user {record.user.username}"
            
            # Attempt to delete
            record.delete()
            
            # Log successful deletion
            logger.info(f"Successfully deleted {record_info}")
            
            messages.success(request, 'Attendance record deleted successfully')
            return redirect('hr_attendance_dashboard')
            
        except AttendanceRecord.DoesNotExist:
            messages.error(request, 'Attendance record not found')
            return redirect('hr_attendance_dashboard')
            
        except Exception as e:
            # Log the error
            logger.error(f"Failed to delete attendance record {record_id}: {str(e)}")
            
            # User-friendly error message
            messages.error(request, 'Failed to delete attendance record. Please try again.')
            return redirect('hr_attendance_dashboard')
    
    # Non-POST requests
    messages.warning(request, 'Invalid request method')
    return redirect('hr_attendance_dashboard')

@login_required(login_url='/hrms_app/login/')

def create_attendance_record(request):
    """Create a new attendance record manually"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            punch_in_time = data.get('punch_in_time')
            punch_out_time = data.get('punch_out_time')
            punch_in_note = data.get('punch_in_note', '')
            punch_out_note = data.get('punch_out_note', '')
            
            user = get_object_or_404(UserProfile, id=user_id)
            
            record = AttendanceRecord.objects.create(
                user=user,
                punch_in_time=datetime.fromisoformat(punch_in_time.replace('Z', '+00:00')),
                punch_out_time=datetime.fromisoformat(punch_out_time.replace('Z', '+00:00')),
                punch_in_note=punch_in_note,
                punch_out_note=punch_out_note,
                row_created_by=request.user.username
            )
            
            return JsonResponse({'success': True, 'message': 'Record created successfully', 'record_id': record.id})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



@login_required(login_url='/hrms_app/login/')

def attendance_analytics(request):
    """Get attendance analytics data for charts"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    start_datetime = datetime.combine(parse_date(start_date), datetime.min.time())
    end_datetime = datetime.combine(parse_date(end_date), datetime.max.time())
    
    # Daily attendance count
    daily_attendance = AttendanceRecord.objects.filter(
        punch_in_time__range=(start_datetime, end_datetime)
    ).extra(
        select={'day': 'date(punch_in_time)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Employee attendance summary
    employee_summary = AttendanceRecord.objects.filter(
        punch_in_time__range=(start_datetime, end_datetime)
    ).values('user__username').annotate(
        total_records=Count('id'),
        avg_duration=Avg('duration'),
        late_arrivals=Count('id', filter=Q(punch_in_time__time__gt=datetime.strptime('09:00', '%H:%M').time()))
    ).order_by('-total_records')
    
    return JsonResponse({
        'daily_attendance': list(daily_attendance),
        'employee_summary': list(employee_summary)
    }) 