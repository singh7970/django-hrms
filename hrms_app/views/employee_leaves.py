import datetime
from django.http import JsonResponse
from django.shortcuts import render
from hrms_app.models import UserProfile, LeaveTypes, UserLeaveMapping
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from django.core.paginator import Paginator
@login_required
def employee_leave_assignment_page(request):
    current_year = datetime.datetime.now().year
    all_users = UserProfile.objects.all()
    leave_types = LeaveTypes.objects.all()

    search_term = request.GET.get("search", "").strip().lower()

    mappings = []

    for user in all_users:
        full_name = user.get_full_name() or user.username
        if search_term and search_term not in full_name.lower():
            continue  # Skip users who don't match search

        default_leave_type = leave_types.first()
        user_mappings = UserLeaveMapping.objects.filter(
            user_profile=user,
            year=current_year,
            is_active=True
        )

        if user_mappings.exists():
            mapping = user_mappings.first()
        else:
            mapping = UserLeaveMapping.objects.create(
                user_profile=user,
                leave_type=default_leave_type,
                total_leaves=default_leave_type.days,
                used_leaves=0,
                remaining_leaves=default_leave_type.days,
                year=current_year,
                row_created_by=request.user.username
            )

        mappings.append({
            "user_id": user.id,
            "user_name": full_name,
            "leave_type_id": mapping.leave_type.id,
            "total": mapping.total_leaves,
            "used": mapping.used_leaves,
            "remaining": mapping.remaining_leaves
        })

    paginator = Paginator(mappings, 5)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "leave_types": leave_types,
        "search_term": search_term,
    }
    return render(request, 'employee_leaves.html', context)

@login_required
@require_GET
def get_leave_mapping(request):
    user_id = request.GET.get('user_id')
    leave_type_id = request.GET.get('leave_type_id')
    current_year = datetime.datetime.now().year

    if not user_id or not leave_type_id:
        return JsonResponse({'error': 'Missing user_id or leave_type_id'}, status=400)

    try:
        user = UserProfile.objects.get(id=user_id)
        leave_type = LeaveTypes.objects.get(id=leave_type_id)
    except (UserProfile.DoesNotExist, LeaveTypes.DoesNotExist):
        return JsonResponse({'error': 'Invalid user or leave type'}, status=404)

    mapping = UserLeaveMapping.objects.filter(
        user_profile=user,
        leave_type=leave_type,
        year=current_year,
        is_active=True
    ).first()

    if not mapping:
        # Auto-create mapping using default leave days
        mapping = UserLeaveMapping.objects.create(
            user_profile=user,
            leave_type=leave_type,
            total_leaves=leave_type.days,
            used_leaves=0,
            year=current_year,
            row_created_by=request.user.username
        )

    return JsonResponse({
        'total': mapping.total_leaves,
        'used': mapping.used_leaves,
        'remaining': mapping.remaining_leaves
    })

@csrf_exempt
@login_required
def update_leave_mapping(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            leave_type_id = data.get("leave_type_id")
            total = float(data.get("total_leaves", 0))
            used = float(data.get("used_leaves", 0))
            remaining = total - used

            mapping = UserLeaveMapping.objects.get(
                user_profile_id=user_id,
                leave_type_id=leave_type_id,
                year=datetime.datetime.now().year
            )

            mapping.total_leaves = total
            mapping.used_leaves = used
            mapping.remaining_leaves = remaining
            mapping.row_modified_by = request.user.username
            mapping.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
@csrf_exempt
@login_required
def add_leave_mapping(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            leave_type_id = data.get("leave_type_id")
            total = float(data.get("total_leaves", 0))
            used = float(data.get("used_leaves", 0))
            remaining = total - used

            # Avoid duplicate
            if UserLeaveMapping.objects.filter(
                user_profile_id=user_id,
                leave_type_id=leave_type_id,
                year=datetime.datetime.now().year,
                is_active=True
            ).exists():
                return JsonResponse({'error': 'Mapping already exists'}, status=400)

            UserLeaveMapping.objects.create(
                user_profile_id=user_id,
                leave_type_id=leave_type_id,
                total_leaves=total,
                used_leaves=used,
                remaining_leaves=remaining,
                year=datetime.datetime.now().year,
                is_active=True,
                row_created_by=request.user.username
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

