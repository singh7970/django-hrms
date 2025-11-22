
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from ..models import UserProfile, UserGroup, LeaveTypes,AppliedLeaves,UserLeaveMapping

def is_authority_user(user_profile):
   
    return UserGroup.objects.filter(authority_user=user_profile).exists()

@login_required
def assign_leave(request):
    user_profile = request.user

    if not UserGroup.objects.filter(authority_user=user_profile).exists():
        messages.error(request, "You don't have permission to assign leaves")
        return redirect('dashboard')

    team_members = UserProfile.objects.select_related('job_details').filter(
    employee_groups__authority_user=user_profile,
    is_active=True
).distinct()

    leave_types = LeaveTypes.objects.filter(is_active=True)
    success_flag = False

    if request.method == 'POST':
        try:
            with transaction.atomic():
                employee_id = request.POST.get('employee_id')
                leave_type_id = request.POST.get('leave_type')
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')
                reason = request.POST.get('reason', '')
                assignment_type = request.POST.get('assignment_type', 'direct')

                if not all([employee_id, leave_type_id, start_date, end_date]):
                    messages.error(request, "All required fields must be filled")
                    return render(request, 'assign_leave.html', {
                        'team_members': team_members,
                        'leave_types': leave_types
                    })

                employee = get_object_or_404(UserProfile, id=employee_id)
                leave_type = get_object_or_404(LeaveTypes, id=leave_type_id)

                if not UserGroup.objects.filter(emp_user=employee, authority_user=user_profile).exists():
                    messages.error(request, "You don't have authority over this employee")
                    return render(request, 'assign_leave.html', {
                        'team_members': team_members,
                        'leave_types': leave_types
                    })

                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()

                if start > end:
                    messages.error(request, "Start date cannot be after end date")
                    return render(request, 'assign_leave.html', {
                        'team_members': team_members,
                        'leave_types': leave_types
                    })

               
                current = start
                total_days = 0.0
                leave_dates = []

                while current <= end:
                    if current.weekday() < 5: 
                        date_str = current.strftime('%Y-%m-%d')
                        duration = request.POST.get(f'duration_{date_str}', 'full') if start != end else request.POST.get('duration', 'full')
                        leave_dates.append((current, duration))
                        total_days += 1.0 if duration == 'full' else 0.5
                    current += timedelta(days=1)

              
                overlap = AppliedLeaves.objects.filter(
                    user_profile=employee,
                    leave_date__in=[date for date, _ in leave_dates],
                    status__in=['Pending', 'Approved']
                )
                if overlap.exists():
                    messages.error(request, "Employee already has leave on one or more selected dates")
                    return redirect('assign_leave') 
              
                current_year = timezone.now().year
                balance, _ = UserLeaveMapping.objects.get_or_create(
                    user_profile=employee, 
                    leave_type=leave_type,
                    year=current_year,
                    defaults={
                        'total_leaves': 0.0,
                        'used_leaves': 0.0,
                        'remaining_leaves': 0.0
                    }
                )

                if balance.remaining_leaves < total_days:
                    messages.error(request, f"Insufficient balance. Required: {total_days}, Available: {balance.remaining_leaves}")
                    return render(request, 'assign_leave.html', {
                        'team_members': team_members,
                        'leave_types': leave_types
                    })
  
                for leave_date, duration in leave_dates:
                    AppliedLeaves.objects.create(
                        user_profile=employee,
                        leave_type=leave_type,
                        leave_date=leave_date,
                        duration=duration,
                        reason=reason,
                        status='Approved' if assignment_type == 'direct' else 'Pending',
                        row_created_by=user_profile.username,
                        row_modified_by=user_profile.username
                    )

               
                if assignment_type == 'direct':
                    balance.used_leaves += total_days
                    balance.remaining_leaves -= total_days
                    balance.save()

                success_flag = True
                messages.success(request, f"Leave successfully {'assigned' if assignment_type == 'direct' else 'requested'} for {employee.first_name}")
                # return redirect('assign_leave') 

        except Exception as e:
          
           
            messages.error(request, f"Error assigning leave: {str(e)}")

    return render(request, 'assign_leave.html', {
        'team_members': team_members,
        'leave_types': leave_types,
        'success_flag': success_flag
    })
@login_required
@require_GET
def get_leave_balance(request):
    employee_id = request.GET.get('employee_id')
    leave_type_id = request.GET.get('leave_type_id')

    try:
        print("🧪 employee_id:", employee_id, "leave_type_id:", leave_type_id)

        user_profile = request.user

        if not UserGroup.objects.filter(authority_user=user_profile).exists():
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        if not employee_id or not leave_type_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        employee = get_object_or_404(UserProfile, id=employee_id)
        leave_type = get_object_or_404(LeaveTypes, id=leave_type_id)

        if not UserGroup.objects.filter(emp_user=employee, authority_user=user_profile).exists():
            return JsonResponse({'error': 'Unauthorized access to employee'}, status=403)

        current_year = timezone.now().year
        leave_balance, _ = UserLeaveMapping.objects.get_or_create(
            user_profile=employee,
            leave_type=leave_type,
            year=current_year,
            defaults={
                'total_leaves': 0.0,
                'used_leaves': 0.0,
                'remaining_leaves': 0.0
            }
        )

        return JsonResponse({
            'balance': float(leave_balance.remaining_leaves),
            'allocated': float(leave_balance.total_leaves),
            'used': float(leave_balance.used_leaves)
        })

    except Exception as e:
        
        
        return JsonResponse({'error': 'Internal server error'}, status=500)