import datetime
import json
import traceback
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from hrms_app.models.leave_types import LeaveTypes
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from ..models.user_leave_mapping import UserLeaveMapping

@login_required
def leave_types_page(request):
    leave_types = LeaveTypes.objects.all().order_by('-row_create_date')
    return render(request, 'leave_type.html', {'leave_types': leave_types})

@login_required
@require_POST
def add_leave_type(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        code = data.get('code')
        days = data.get('days')

        if LeaveTypes.objects.filter(name=name).exists() or LeaveTypes.objects.filter(code=code).exists():
            return JsonResponse({'error': 'Leave type with same name or code already exists.'}, status=400)

        LeaveTypes.objects.create(
            name=name,
            code=code,
            days=days,
            row_created_by=request.user.username
        )

        return JsonResponse({'message': 'Leave type added successfully.'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
def update_leave_type(request, id):  
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            code = data.get("code")
            days = float(data.get("days"))

            leave_type = LeaveTypes.objects.get(id=id)  
            leave_type.name = name
            leave_type.code = code
            leave_type.days = days
            leave_type.save()

            
            current_year = datetime.datetime.now().year
            mappings = UserLeaveMapping.objects.filter(
                leave_type_id=id,
                year=current_year,
                is_active=True
            )

            for mapping in mappings:
                if round(mapping.total_leaves - mapping.used_leaves, 2) == round(mapping.remaining_leaves, 2):
                    mapping.total_leaves = days
                    mapping.remaining_leaves = days - mapping.used_leaves
                    mapping.row_modified_by = request.user.username
                    mapping.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def delete_leave_type(request, id):
    leave_type = get_object_or_404(LeaveTypes, pk=id)
    leave_type.delete()
    messages.success(request, 'Leave type deleted.')
    return redirect('leave_types_page')
