from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from hrms_app.models.time_attendance_record import AttendanceRecord
from hrms_app.models.holiday import Holiday
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from hrms_app.constants import MAX_WORK_HOURS
import logging
logger = logging.getLogger('hrms_app')

@login_required(login_url='/hrms_app/login/')
def punch_in_out_page(request):
    latest_record = AttendanceRecord.objects.filter(user=request.user).order_by('-row_created_date').first()
    disable_punch = False
    block_access = False
    weekend_restriction = False
    weekend_message = ""
    
    # Check if today is weekend (Saturday = 5, Sunday = 6)
    today = timezone.now()
    today_date = today.date()
    
    if today.weekday() in [5, 6]:  # Saturday or Sunday
        weekend_restriction = True
        day_name = "Saturday" if today.weekday() == 5 else "Sunday"
        weekend_message = f"Punch in/out is not allowed on {day_name}."
        disable_punch = True
        logger.info(f"Weekend restriction: {day_name} - punch disabled")
    
    # Check if today is a holiday
    is_holiday_today = Holiday.objects.filter(date=today_date, is_active=True).exists()
    holiday_info = None
    holiday_restriction = False
    holiday_message = ""
    
    if is_holiday_today:
        holiday_info = Holiday.objects.filter(date=today_date, is_active=True).first()
        holiday_restriction = True
        holiday_message = f"Today is {holiday_info.occasion}. All attendance functions are disabled on holidays."
        disable_punch = True
        logger.info(f"Holiday restriction: {holiday_info.occasion} - all functions disabled")
    
    if latest_record and not weekend_restriction and not holiday_restriction:
        logger.info(f"Latest record status: {latest_record.status}")

        if latest_record.status == "PUNCHED_IN" and latest_record.punch_out_time is None:
            time_calculate = timezone.now() - latest_record.punch_in_time
            logger.info(f"Time elapsed: {time_calculate}")
            if time_calculate.total_seconds() > MAX_WORK_HOURS * 3600:
                disable_punch = True
                # block_access = True
                logger.info(f"Punching disabled: exceeded {MAX_WORK_HOURS} hours.")
               

    return render(request, 'time.html', {
        'data': latest_record,
        'disable_punch': disable_punch,
        'block_access': block_access,
        'weekend_restriction': weekend_restriction,
        'weekend_message': weekend_message,
        'holiday_restriction': holiday_restriction,
        'holiday_message': holiday_message,
        'holiday_info': holiday_info,
    })


@login_required(login_url='/hrms_app/login/')
def save_punch_in_data(request):
    logger.info("call save_punch_in_data API")

    if request.method == 'POST':
        now = timezone.now()
        today_date = now.date()
        
        # Check if today is weekend (Saturday = 5, Sunday = 6)
        if now.weekday() in [5, 6]:
            day_name = "Saturday" if now.weekday() == 5 else "Sunday"
            logger.warning(f"Punch in attempted on {day_name} - blocked")
            return JsonResponse({
                'success': False, 
                'message': f'Punch in is not allowed on {day_name}.'
            })
        
        # Check if today is a holiday
        holiday_today = Holiday.objects.filter(date=today_date, is_active=True).first()
        if holiday_today:
            logger.warning(f"Punch in attempted on holiday: {holiday_today.occasion} - blocked")
            return JsonResponse({
                'success': False, 
                'message': f'Punch in is not allowed on holidays. Today is {holiday_today.occasion}.'
            })
        
        note = request.POST.get('note', '').strip()
        
        logger.info(f"User: {request.user} ")
        AttendanceRecord.objects.create(
            user=request.user,
            punch_in_time=now,
            punch_in_note=note,
            
        )
       
        logger.info("Punched in successfully")
        return JsonResponse({'success': True,'message': 'Punched in successfully!'})
    logger.warning("Invalid request")
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required(login_url='/hrms_app/login/')
def save_punch_out_data(request):
    logger.info("call punch out urls")
    logger.info(f"User: {request.user} ")

    if request.method == 'POST':
        now = timezone.now()
        today_date = now.date()
        
        # Check if today is weekend (Saturday = 5, Sunday = 6)
        if now.weekday() in [5, 6]:
            day_name = "Saturday" if now.weekday() == 5 else "Sunday"
            logger.warning(f"Punch out attempted on {day_name} - blocked")
            return JsonResponse({
                'success': False, 
                'message': f'Punch out is not allowed on {day_name}.'
            })
        
        # Check if today is a holiday
        holiday_today = Holiday.objects.filter(date=today_date, is_active=True).first()
        if holiday_today:
            logger.warning(f"Punch out attempted on holiday: {holiday_today.occasion} - blocked")
            return JsonResponse({
                'success': False, 
                'message': f'Punch out is not allowed on holidays. Today is {holiday_today.occasion}.'
            })
        
        note = request.POST.get('note', '').strip()
        logger.info(f"note- : {note}")
       
        try:
            record = AttendanceRecord.objects.filter(user=request.user).latest('punch_in_time')
            record.punch_out_time = now
            record.punch_out_note = note
            
            record.save()  # This automatically calculates duration
            
            # Calculate work details
            duration_seconds = int(record.duration) if record.duration else 0
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_formatted = f"{hours}.{minutes:02d}.{seconds:02d}"
            
            # Determine work type
            work_type = "Full Day" if record.is_full_day() else "Half Day"
            
            # Calculate total hours as decimal
            total_hours = round(duration_seconds / 3600, 2) if duration_seconds > 0 else 0
            
            return JsonResponse({
                'success': True, 
                'message': 'Punched out successfully!',
                'duration': duration_formatted,
                'total_hours': total_hours,
                'work_type': work_type,
                'punch_in': record.punch_in_time.strftime('%H:%M'),
                'punch_out': record.punch_out_time.strftime('%H:%M')
            })
        except AttendanceRecord.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No active punch-in record found.'})

    return JsonResponse({'success': False, 'message': 'Invalid request'})



