from datetime import date, datetime
from calendar import monthrange
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from hrms_app.models.time_attendance_record import AttendanceRecord
from hrms_app.models.holiday import Holiday
from hrms_app.models.applied_leaves import AppliedLeaves


@login_required(login_url='/hrms_app/login/')
def time_dashboard_page(request):
    user = request.user
    today = date.today()
    now = datetime.now()
    joining_date = user.date_joined.date()

    # Parse selected month/year or default to current
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    try:
        month = int(selected_month) if selected_month else today.month
        year = int(selected_year) if selected_year else today.year
    except ValueError:
        month = today.month
        year = today.year

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    visible_start_date = max(joining_date, first_day)

    # Fetch attendance records for user in selected month
    records = AttendanceRecord.objects.filter(
        user=user,
        punch_in_time__date__range=(visible_start_date, last_day)
    )

    # Fetch holidays in the selected month
    holidays = Holiday.objects.filter(date__range=(first_day, last_day), is_active=True)
    holiday_dates = {h.date: h.occasion for h in holidays}
    
    # Fetch sick leave records for the user in selected month
    sick_leaves = AppliedLeaves.objects.filter(
        user_profile=user,
        leave_type__code__iexact='SL',  # Sick Leave
        status='Approved',
        leave_date__range=(first_day, last_day)
    )
    sick_leave_dates = {leave.leave_date: 'Sick Leave' for leave in sick_leaves}

    # Build initial day → status map
    status_map = {}
    for day in range(1, last_day.day + 1):
        current_date = date(year, month, day)

        # Skip days before user joined
        if current_date < joining_date:
            continue

        if current_date in holiday_dates:
            status = "holiday"
        elif current_date in sick_leave_dates:
            status = "sick"
        else:
            weekday = current_date.weekday()  # Monday = 0, Sunday = 6
            if weekday in [5, 6]:
                status = "unrecorded"
            elif current_date == today and now.hour < 18:
                status = "unrecorded"
            elif current_date > today:
                status = "unrecorded"
            else:
                status = "absent"

        status_map[day] = status

    # Create a record map for tooltip data
    record_map = {}
    
    # Overwrite with actual attendance records
    for record in records:
        punch_date = record.punch_in_time.date()
        if visible_start_date <= punch_date <= last_day:
            day = punch_date.day
            
            # Store record data for tooltip
            duration_formatted = None
            if record.duration:
                total_seconds = int(record.duration)
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_formatted = f"{hours}.{minutes:02d}.{seconds:02d}"
            
            record_map[day] = {
                'duration': duration_formatted,
                'punch_in': record.punch_in_time.strftime('%H:%M') if record.punch_in_time else None,
                'punch_out': record.punch_out_time.strftime('%H:%M') if record.punch_out_time else None,
                'status': record.punch_out_time is not None
            }
            
            if record.punch_out_time:
                if record.is_full_day():
                    status_map[day] = "present"
                else:
                    status_map[day] = "halfday"
            else:
                if punch_date == today:
                    status_map[day] = "punchin"


    # Summary counts
    present_days = sum(1 for status in status_map.values() if status == "present")
    half_days = sum(1 for status in status_map.values() if status == "halfday")
    absent_days = sum(1 for status in status_map.values() if status == "absent")
    sick_days = sum(1 for status in status_map.values() if status == "sick")  
    holiday_days = sum(1 for status in status_map.values() if status == "holiday")

    # Build calendar grid
    weekday_index = (first_day.weekday() + 1) % 7  # Adjust to Sunday = 0
    calendar_cells = []

    # Empty leading slots
    for _ in range(weekday_index):
        calendar_cells.append({'day': '', 'status': ''})

    # Day-wise calendar cells
    for day in range(1, last_day.day + 1):
        cell_date = date(year, month, day)
        if cell_date < joining_date:
            cell_status = ''  # Don't show anything before joining
        else:
            cell_status = status_map.get(day, 'unrecorded')

        # Get tooltip data for this day
        tooltip_data = record_map.get(day, {})
        
        calendar_cells.append({
            'day': day,
            'status': cell_status,
            'holiday': holiday_dates.get(cell_date),  # None if not holiday
            'duration': tooltip_data.get('duration'),
            'punch_in': tooltip_data.get('punch_in'),
            'punch_out': tooltip_data.get('punch_out'),
            'has_record': tooltip_data.get('status', False)
        })

    return render(request, 'time_dashboard.html', {
        'calendar_cells': calendar_cells,
        'attendance_status': status_map,
        'current_month': month,
        'current_year': year,
        'holidays': holidays,
        'present_days': present_days,
        'half_days': half_days,
        'absent_days': absent_days,
        'sick_days': sick_days,
        'holiday_days': holiday_days,
        'today': today,  
    })
