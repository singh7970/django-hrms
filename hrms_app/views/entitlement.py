
import bs4
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.contrib import messages
from ..models import UserLeaveMapping, LeaveTypes
from datetime import datetime, date
import logging
# from django.template.loader import get_template
from django.template import Context
from django.http import JsonResponse
from django.template.loader import render_to_string
logger = logging.getLogger(__name__)

@login_required
def leave_entitlements_view(request):
    try:
        user_profile = request.user
        current_year = timezone.now().year

        entitlements_qs = UserLeaveMapping.objects.select_related(
            'leave_type', 'user_profile'
        ).filter(
            user_profile=user_profile,
            is_active=True
        ).order_by('-year', 'leave_type__name')

        leave_types = LeaveTypes.objects.filter(is_active=True).order_by('name')

        leave_type_filter = request.GET.get('leave_type')
        # start_date_filter = request.GET.get('start_date')
        # end_date_filter = request.GET.get('end_date')

        if leave_type_filter:
           entitlements_qs = entitlements_qs.filter(leave_type__name__iexact=leave_type_filter)

        start_date_filter = request.GET.get('start_date')
        end_date_filter = request.GET.get('end_date')

        if start_date_filter:
          try:
             start_date_obj = datetime.strptime(start_date_filter, '%Y-%m-%d').date()
             entitlements_qs = entitlements_qs.filter(valid_from__gte=start_date_obj)
          except Exception as e:
             print("Invalid start_date format:", start_date_filter, e)

        if end_date_filter:
          try:
             end_date_obj = datetime.strptime(end_date_filter, '%Y-%m-%d').date()
             entitlements_qs = entitlements_qs.filter(valid_to__lte=end_date_obj)
          except Exception as e:
              print("Invalid end_date format:", end_date_filter, e)
                

        totals = entitlements_qs.aggregate(
            total_allocated=Sum('total_leaves'),
            total_used=Sum('used_leaves'),
            total_remaining=Sum('remaining_leaves')
        )

        total_days = totals.get('total_allocated') or 0
        total_used = totals.get('total_used') or 0
        total_remaining = totals.get('total_remaining') or 0

        paginator = Paginator(entitlements_qs, 20)
        page_number = request.GET.get('page', 1)

        try:
            page_number = int(page_number)
        except (ValueError, TypeError):
            page_number = 1

        entitlements = paginator.get_page(page_number)

        for entitlement in entitlements:
            entitlement.valid_from = date(entitlement.year, 1, 1)
            entitlement.valid_to = date(entitlement.year, 12, 31)
            entitlement.remaining_days = entitlement.total_leaves - entitlement.used_leaves
            entitlement.total_days = entitlement.total_leaves
            entitlement.used_days = entitlement.used_leaves

        context = {
            'entitlements': entitlements,
            'leave_types': leave_types,
            'total_days': round(total_days, 1),
            'total_used': round(total_used, 1),
            'total_remaining': round(total_remaining, 1),
            'record_count': entitlements_qs.count(),
            'current_year': current_year,
            'selected_leave_type': leave_type_filter,
            'selected_start_date': start_date_filter,
            'selected_end_date': end_date_filter,
            'has_pagination': entitlements.has_other_pages(),
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
           table_html = render_to_string('entitlements.html', {**context, 'only_table': True}, request=request)
           soup = bs4.BeautifulSoup(table_html, 'html.parser')
           rows = soup.select_one('#entitlementTable').decode_contents()
           return JsonResponse({
            'table_html': rows,
            'record_count': entitlements_qs.count()
            })

        return render(request, 'entitlements.html', context)

    except Exception as e:
        logger.exception(f"Error in leave_entitlements_view for user {request.user.username}: {str(e)}")
        messages.error(request, "An error occurred while loading entitlements.")
        return render(request, 'entitlements.html', {
            'entitlements': [],
            'leave_types': LeaveTypes.objects.filter(is_active=True),
            'total_days': 0,
            'total_used': 0,
            'total_remaining': 0,
            'record_count': 0,
            'current_year': timezone.now().year,
            'selected_leave_type': '',
            'selected_start_date': '',
            'selected_end_date': '',
            'has_pagination': False,
        })


@login_required 
def get_leave_summary_api(request):
    """
    API endpoint to get leave summary data (for AJAX calls if needed)
    """
    try:
        user_profile = request.user.userprofile
        current_year = timezone.now().year
        
        # Get summary data for current year
        summary = UserLeaveMapping.objects.filter(
            user_profile=user_profile,
            year=current_year,
            is_active=True
        ).aggregate(
            total_allocated=Sum('total_leaves'),
            total_used=Sum('used_leaves'),
            total_remaining=Sum('remaining_leaves')
        )
        
        # Get leave type breakdown
        leave_breakdown = UserLeaveMapping.objects.select_related('leave_type').filter(
            user_profile=user_profile,
            year=current_year,
            is_active=True
        ).values(
            'leave_type__name',
            'leave_type__code',
            'total_leaves',
            'used_leaves',
            'remaining_leaves'
        ).order_by('leave_type__name')
        
        response_data = {
            'success': True,
            'summary': {
                'total_allocated': summary.get('total_allocated') or 0,
                'total_used': summary.get('total_used') or 0,
                'total_remaining': summary.get('total_remaining') or 0,
            },
            'breakdown': list(leave_breakdown),
            'year': current_year
        }
        
        from django.http import JsonResponse
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_leave_summary_api for user {request.user.username}: {str(e)}")
        from django.http import JsonResponse
        return JsonResponse({'success': False, 'error': 'Failed to fetch leave summary'}, status=500)