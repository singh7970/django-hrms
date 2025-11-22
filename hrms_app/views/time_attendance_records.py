from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from hrms_app.models.time_attendance_record import AttendanceRecord
from django.utils.dateparse import parse_date
from datetime import datetime, date
from django.template.loader import render_to_string
from django.http import JsonResponse



@login_required(login_url='/hrms_app/login/')
def attendance_records(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    user = request.user
    today = date.today().isoformat()

    records = AttendanceRecord.objects.none()  #Khaliii
    
    if start_date or end_date:
        # Apply filters if date range is provided
        filters = {'user': user}
        if start_date:
            filters['punch_in_time__gte'] = datetime.combine(parse_date(start_date), datetime.min.time())  # type: ignore
        if end_date:
            filters['punch_in_time__lte'] = datetime.combine(parse_date(end_date), datetime.max.time())  # type: ignore

        records = AttendanceRecord.objects.filter(**filters).order_by('-row_created_date')
    else:
        # No filters = show only the latest record
        latest_record = AttendanceRecord.objects.filter(user=user).order_by('-row_created_date').first()
        if latest_record:
            records = [latest_record]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        table_html = render_to_string('attendance_table.html', {'records': records})
        return JsonResponse({'table_html': table_html})

    context = {
        'records': records,
        'today': today,
        
    }
    return render(request, 'time_records.html', context)
