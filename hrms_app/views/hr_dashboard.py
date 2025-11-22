from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import date
from hrms_app.models import UserProfile, AppliedLeaves, UserRole

def is_hr(user):
    try:
        return user.userrole.role.name.lower() == 'admin'
    except:
        return False

@login_required
def hr_main_dashboard(request):
    if not is_hr(request.user):
        return redirect('employee_dashboard')

    today = date.today()

    total_employees = UserProfile.objects.count()
    on_leave_today = AppliedLeaves.objects.filter(
        leave_date=today,
        status='Approved'
    ).count()
    pending_leaves = AppliedLeaves.objects.filter(status='Pending').count()

    context = {
        'total_employees': total_employees,
        'on_leave_today': on_leave_today,
        'pending_leaves': pending_leaves,
    }

    return render(request, 'hr_dashboard.html', context)