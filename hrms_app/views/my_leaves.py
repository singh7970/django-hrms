from datetime import date, datetime, timedelta
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, F, Sum
from ..models.user_leave_mapping import UserLeaveMapping
from ..models.applied_leaves import AppliedLeaves
from ..models.leave_types import LeaveTypes

@login_required(login_url='/hrms_app/login/')
def my_leave(request):
    user_profile = request.user
    status_filter = request.GET.get('status', 'all')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    page_number = request.GET.get('page', 1)

    # Get leave balances for the current user
    leave_balances = UserLeaveMapping.objects.filter(
        user_profile=user_profile,
        is_active=True
    ).select_related('leave_type')

    # Extract leave balances
    balances = {lb.leave_type.code.upper(): lb.remaining_leaves for lb in leave_balances}
    casual_leave_balance = balances.get('CL', 0)
    sick_leave_balance = balances.get('SL', 0)
    earned_leave_balance = balances.get('LWP', 0)
    paid_leave_balance = balances.get('PL', 0)

    # Applied leaves queryset
    applied_leaves_qs = AppliedLeaves.objects.filter(
        user_profile=user_profile,
        # is_active=True
    ).select_related('leave_type')

    # Filter to only current month leaves by default (if no from_date and to_date given)
    if not from_date and not to_date:
        today = date.today()
        first_day = today.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        applied_leaves_qs = applied_leaves_qs.filter(leave_date__range=(first_day, last_day))
    else:
        # Filter by from_date/to_date if provided
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                applied_leaves_qs = applied_leaves_qs.filter(leave_date__gte=from_date_obj)
            except ValueError:
                pass
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                applied_leaves_qs = applied_leaves_qs.filter(leave_date__lte=to_date_obj)
            except ValueError:
                pass

    # Filter by status
    if status_filter != 'all':
        applied_leaves_qs = applied_leaves_qs.filter(status__iexact=status_filter)

    # Group leaves by application using (leave_type_id, row_create_date, reason)
    leaves_grouped = {}
    for leave in applied_leaves_qs:
        key = (leave.leave_type_id, leave.row_create_date, leave.reason)

        if key not in leaves_grouped:
            leaves_grouped[key] = {
                'id': leave.id,
                'leave_type': leave.leave_type,
                'start_date': leave.leave_date,
                'end_date': leave.leave_date,
                'days': 0,
                'created_at': leave.row_create_date,
                'status': leave.status,
                'reason': leave.reason,
                'duration': leave.duration,
                'dates': [],
                'cancel_allowed': False,
            }

        group = leaves_grouped[key]
        group['dates'].append(leave.leave_date)

        # Update start and end dates
        if leave.leave_date < group['start_date']:
            group['start_date'] = leave.leave_date
        if leave.leave_date > group['end_date']:
            group['end_date'] = leave.leave_date

        # Calculate days (0.5 for half day)
        if leave.duration in ['half_morning', 'half_evening']:
            group['days'] += 0.5
        else:
            group['days'] += 1

    # Determine cancel eligibility: cancel allowed only if status = Pending
    # and today <= leave_date - 1 day (only cancel up to day before leave)
    today = date.today()
    for group in leaves_grouped.values():
        if group['status'].lower() == 'pending':
            # If any leave date in group is at least 1 day ahead
            if any((ldate - timedelta(days=1)) >= today for ldate in group['dates']):
                group['cancel_allowed'] = True

    # Sort leaves by created_at desc
    grouped_leaves = sorted(leaves_grouped.values(), key=lambda x: x['created_at'], reverse=True)

    # Pagination (10 per page)
    paginator = Paginator(grouped_leaves, 20)
    applied_leaves = paginator.get_page(page_number)

    context = {
        'casual_leave_balance': casual_leave_balance,
        'sick_leave_balance': sick_leave_balance,
        'earned_leave_balance': earned_leave_balance,
        'paid_leave_balance': paid_leave_balance,
        'applied_leaves': applied_leaves,
        'status_filter': status_filter,
        'from_date': from_date,
        'to_date': to_date,
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
       return render(request, 'my_leave.html', context)
    
    return render(request, 'my_leave.html', context)


@login_required(login_url='/hrms_app/login/')
def get_leave_details(request):
    leave_id = request.GET.get('id')
    if not leave_id:
        return JsonResponse({'error': 'Leave ID not provided'}, status=400)

    try:
        main_leave = AppliedLeaves.objects.select_related('leave_type').get(
            id=leave_id,
            user_profile=request.user
        )

        # Get related leaves by application key
        related_leaves = AppliedLeaves.objects.filter(
            user_profile=request.user,
            leave_type=main_leave.leave_type,
            row_create_date=main_leave.row_create_date,
            reason=main_leave.reason
        ).order_by('leave_date')

        total_days = sum(
            0.5 if leave.duration in ['half_morning', 'half_evening'] else 1
            for leave in related_leaves
        )

        daily_durations = {}
        for leave in related_leaves:
            date_str = leave.leave_date.strftime('%d %b %Y')
            if leave.duration == 'half_morning':
                daily_durations[date_str] = 'Half Day (Morning)'
            elif leave.duration == 'half_evening':
                daily_durations[date_str] = 'Half Day (Evening)'
            else:
                daily_durations[date_str] = 'Full Day'

        response_data = {
            'leave_type': f"{main_leave.leave_type.name} ({main_leave.leave_type.code})",
            'start_date': related_leaves.first().leave_date.strftime('%d %b %Y'),
            'end_date': related_leaves.last().leave_date.strftime('%d %b %Y'),
            'days': total_days,
            'applied_on': main_leave.row_create_date.strftime('%d %b %Y'),
            'status': main_leave.status,
            'reason': main_leave.reason or 'No reason provided',
            'daily_durations': daily_durations,
        }
        return JsonResponse(response_data)

    except AppliedLeaves.DoesNotExist:
        return JsonResponse({'error': 'Leave record not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required(login_url='/hrms_app/login/')
def cancel_leave(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        leave_id = data.get('leave_id')

        if not leave_id:
            return JsonResponse({'error': 'Leave ID not provided'}, status=400)

        # Get the main leave
        main_leave = AppliedLeaves.objects.get(
            id=leave_id,
            user_profile=request.user,
            status='Pending'
        )

        # Get all leave entries in the same group
        leave_group = AppliedLeaves.objects.filter(
            user_profile=request.user,
            leave_type=main_leave.leave_type,
            row_create_date=main_leave.row_create_date,
            reason=main_leave.reason,
            status='Pending'
        )

        # Check if cancellation is allowed
        if any((ld.leave_date - timedelta(days=1)) < date.today() for ld in leave_group):
            return JsonResponse({'error': 'Cancellation period expired for this leave.'}, status=400)

        # Calculate total leave days
        total_days = sum(0.5 if leave.duration in ['half_morning', 'half_evening'] else 1 for leave in leave_group)

        # Cancel all related leaves
        leave_group.update(status='Cancelled', is_active=False)

        # Refund leave balance
        leave_mapping = UserLeaveMapping.objects.get(
            user_profile=request.user,
            leave_type=main_leave.leave_type,
            is_active=True
        )
        leave_mapping.used_leaves = F('used_leaves') - total_days
        leave_mapping.remaining_leaves = F('remaining_leaves') + total_days
        leave_mapping.save()
        leave_mapping.refresh_from_db()  # Get actual values from DB

        return JsonResponse({
            'success': 'Leave cancelled successfully',
            'used_leaves': float(leave_mapping.used_leaves),
            'remaining_leaves': float(leave_mapping.remaining_leaves),
            'leave_type': main_leave.leave_type.name  # Corrected field
        })

    except AppliedLeaves.DoesNotExist:
        return JsonResponse({'error': 'Leave record not found or already cancelled'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)