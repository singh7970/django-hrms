
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from hrms_app.models import AppliedLeaves
from datetime import date
from django.db.models.functions import TruncMonth
from django.db.models import Q, Count
from calendar import monthrange
from django.views.decorators.http import require_POST

from ..models.user_leave_mapping import UserLeaveMapping
from django.utils.dateparse import parse_date

from ..models.users import UserProfile
from ..models.leave_types import LeaveTypes


@login_required
def manage_leaves(request):
    today = date.today()

    
    months = AppliedLeaves.objects.dates('leave_date', 'month', order='DESC')
    months_list = list(months)

    page = int(request.GET.get('page', 1))
    selected_month = months_list[page - 1] if page <= len(months_list) else None

   
    leaves = AppliedLeaves.objects.select_related('user_profile', 'leave_type')

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    if selected_month:
        leaves = leaves.filter(
            leave_date__year=selected_month.year,
            leave_date__month=selected_month.month
        )

    if search:
        leaves = leaves.filter(
            Q(user_profile__email__icontains=search) |
            Q(user_profile__first_name__icontains=search) |
            Q(user_profile__last_name__icontains=search)
        )
    if status:
        leaves = leaves.filter(status=status)
    if date_from:
        leaves = leaves.filter(leave_date__gte=date_from)
    if date_to:
        leaves = leaves.filter(leave_date__lte=date_to)

    
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_ids')
        selected_leaves = AppliedLeaves.objects.filter(id__in=selected_ids)

        for leave in selected_leaves:
            previous_status = leave.status
            duration_map = {
                'full': 1.0,
                'half_morning': 0.5,
                'half_evening': 0.5
            }
            duration = duration_map.get(leave.duration, 0)

            if action in ['reject', 'cancel'] and previous_status in ['Approved', 'Pending']:
                try:
                    mapping = UserLeaveMapping.objects.get(
                        user_profile=leave.user_profile,
                        leave_type=leave.leave_type,
                        is_active=True
                    )
                    mapping.used_leaves -= duration
                    mapping.save()
                except UserLeaveMapping.DoesNotExist:
                    pass  

                leave.status = 'Rejected' if action == 'reject' else 'Cancelled'

            
            elif action == 'approve':
                leave.status = 'Approved'

            
            elif action == 'delete':
                if previous_status in ['Approved', 'Pending']:
                    try:
                        mapping = UserLeaveMapping.objects.get(
                            user_profile=leave.user_profile,
                            leave_type=leave.leave_type,
                            is_active=True
                        )
                        mapping.used_leaves -= duration
                        mapping.save()
                    except UserLeaveMapping.DoesNotExist:
                        pass
                leave.delete()
                continue  

            leave.save()

        return redirect('manage_leaves')

    context = {
        'leaves': leaves.order_by('-leave_date'),
        'months': months_list,
        'current_month': selected_month,
        'page_number': page,
        'total_pages': len(months_list),
        'leave_types': LeaveTypes.objects.filter(is_active=True),
        'request': request,
    }
    return render(request, 'manage_leave.html', context)



@require_POST
def update_leave(request):
    leave_id = request.POST.get('leave_id')
    leave_type_id = request.POST.get('leave_type')

    print("leave_type:", leave_type_id)
    print("leave_id:", leave_id)

    if not leave_id or not leave_type_id:
       
        return redirect('manage_leaves')

    leave = get_object_or_404(AppliedLeaves, id=leave_id)
    leave_type = get_object_or_404(LeaveTypes, id=leave_type_id)

    leave.leave_type = leave_type
    leave.leave_date = request.POST.get('leave_date')
    leave.duration = request.POST.get('duration')
    leave.status = request.POST.get('status')
    leave.reason = request.POST.get('reason')
    leave.save()
    
    return redirect('manage_leaves')


@login_required
@require_POST
def add_leave(request):
    email = request.POST.get("email")
    leave_type_id = request.POST.get("leave_type")
    leave_date = parse_date(request.POST.get("leave_date"))
    duration_str = request.POST.get("duration")  
    status = request.POST.get("status")
    reason = request.POST.get("reason")

    duration_map = {
        'full': 1.0,
        'half_morning': 0.5,
        'half_evening': 0.5
    }

    if duration_str not in duration_map:
        messages.error(request, "Invalid leave duration.")
        return redirect('manage_leaves')

    duration = duration_map[duration_str]

    try:
        user = UserProfile.objects.get(email=email)
        leave_type = LeaveTypes.objects.get(id=leave_type_id)

        if AppliedLeaves.objects.filter(user_profile=user, leave_date=leave_date).exists():
            messages.error(request, "Leave already applied on this date.")
            return redirect('manage_leaves')

        mapping = UserLeaveMapping.objects.get(user_profile=user, leave_type=leave_type, is_active=True)

        if mapping.remaining_leaves < duration:
            messages.error(request, "Insufficient leave balance.")
            return redirect('manage_leaves')

        AppliedLeaves.objects.create(
            user_profile=user,
            leave_type=leave_type,
            leave_date=leave_date,
            duration=duration_str,  
            status=status,
            reason=reason
        )

       
        if status in ['Approved', 'Pending']:
            mapping.used_leaves += duration
            mapping.save()

        messages.success(request, "Leave added successfully.")

    except UserProfile.DoesNotExist:
        messages.error(request, "User with that email not found.")
    except LeaveTypes.DoesNotExist:
        messages.error(request, "Invalid leave type selected.")
    except UserLeaveMapping.DoesNotExist:
        messages.error(request, "Leave balance record not found for this leave type.")

    return redirect('manage_leaves')