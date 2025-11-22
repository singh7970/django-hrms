from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import AppliedLeaves, LeaveTypes, UserProfile
import json
from hrms_app.models.performance.user_group import UserGroup
from datetime import datetime
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from ..models import AppliedLeaves, LeaveTypes, UserProfile, UserLeaveMapping
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
import logging
from django.shortcuts import get_object_or_404


logger = logging.getLogger(__name__)

@login_required
def leave_list_view(request):
    try:
        employee_ids = UserGroup.objects.filter(authority_user=request.user).values_list('emp_user_id', flat=True)
        logger.info(f"User {request.user} has authority over {len(employee_ids)} employees")
        
        applied_leaves = AppliedLeaves.objects.select_related(
            'user_profile', 'leave_type'
        ).filter(user_profile_id__in=employee_ids).order_by('-leave_date')
        
        leave_types = LeaveTypes.objects.all()
        
        status = request.GET.get('status', 'Pending')
        if status:
            applied_leaves = applied_leaves.filter(status=status)
        
        if request.GET.get('leave_type'):
            applied_leaves = applied_leaves.filter(leave_type_id=request.GET.get('leave_type'))
        
       
        if request.GET.get('from_date'):
            from_date_str = request.GET.get('from_date')
            try:
                from_date = parse_date(from_date_str)
                if from_date:
                    applied_leaves = applied_leaves.filter(leave_date__gte=from_date)
                else:
                    logger.warning(f"Invalid from_date format: {from_date_str}")
            except Exception as e:
                logger.error(f"Error parsing from_date {from_date_str}: {e}")
        
        if request.GET.get('to_date'):
            to_date_str = request.GET.get('to_date')
            try:
                to_date = parse_date(to_date_str)
                if to_date:
                    applied_leaves = applied_leaves.filter(leave_date__lte=to_date)
                else:
                    logger.warning(f"Invalid to_date format: {to_date_str}")
            except Exception as e:
                logger.error(f"Error parsing to_date {to_date_str}: {e}")
        
        if request.GET.get('employee_name'):
            applied_leaves = applied_leaves.filter(user_profile_id=request.GET.get('employee_name'))
         
        employees = UserProfile.objects.filter(id__in=employee_ids)
        
     
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        
            leaves_data = []
            current_year = now().year
            
            for leave in applied_leaves:
                try:
                   
                    leave_balance = get_leave_balance(
                        leave.user_profile.id if leave.user_profile else None, 
                        leave.leave_type.id if leave.leave_type else None, 
                        current_year
                    )
                    
                    
                    employee_name = ""
                    if leave.user_profile:
                        first_name = leave.user_profile.first_name or ""
                        last_name = leave.user_profile.last_name or ""
                        employee_name = f"{first_name} {last_name}".strip()
                    
                    leaves_data.append({
                        'id': leave.id,
                        'leave_date': leave.leave_date.strftime('%Y-%m-%d') if leave.leave_date else '',
                        'employee_name': employee_name,
                        'leave_type': leave.leave_type.name if leave.leave_type else '',
                        'leave_balance': leave_balance,
                        'days': getattr(leave, 'number_of_days', 1),
                        'status': leave.status or '',
                        'reason': getattr(leave, 'reason', '') or getattr(leave, 'comments', '') or ''
                    })
                except Exception as e:
                    logger.error(f"Error processing leave {leave.id}: {e}")
                    continue
            
            return JsonResponse({
                'success': True,
                'leaves': leaves_data,
                'total_count': len(leaves_data)
            })
        
      
        context = {
            'employees': employees,
            'applied_leaves': applied_leaves,
            'leave_types': leave_types,
        }
        return render(request, 'leave_list.html', context)
    
    except Exception as e:
        logger.error(f"Error in leave_list_view: {e}")
       
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
      
        return render(request, 'error.html', {'error_message': str(e)}, status=500)

def get_leave_balance(user_profile_id, leave_type_id, year=None):
    """
    Get the remaining leave balance for a specific user and leave type
    """
    if year is None:
        year = now().year
    
   
    if not user_profile_id or not leave_type_id:
        return 0.0
    
    try:
        user_leave_mapping = UserLeaveMapping.objects.get(
            user_profile_id=user_profile_id,
            leave_type_id=leave_type_id,
            year=year,
            is_active=True
        )
        return user_leave_mapping.remaining_leaves or 0.0
    except UserLeaveMapping.DoesNotExist:
        return 0.0
    except Exception as e:
        logger.error(f"Error getting leave balance for user {user_profile_id}, leave type {leave_type_id}: {e}")
        return 0.0

@csrf_exempt
@login_required
@require_POST
def approve_leave(request, leave_id):
    try:
        data = json.loads(request.body)
        action = data.get("action")

        if action != "approve":
            return JsonResponse({"success": False, "message": "Invalid action"})

        
        employee_ids = UserGroup.objects.filter(
            authority_user=request.user
        ).values_list('emp_user_id', flat=True)

       
        leave = AppliedLeaves.objects.get(id=leave_id, user_profile_id__in=employee_ids)

      
        leave.status = "Approved"
        leave.row_modified_by = request.user.username
        leave.save()

        return JsonResponse({"success": True})

    except AppliedLeaves.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Leave not found or you do not have permission to approve this leave"
        }, status=403)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def reject_leave(request, leave_id):
    try:
      
        employee_ids = UserGroup.objects.filter(authority_user=request.user).values_list('emp_user_id', flat=True)

        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}

        leave = AppliedLeaves.objects.get(
            id=leave_id,
            user_profile_id__in=employee_ids  
        )

        if leave.status == 'Rejected':
            return JsonResponse({
                'success': False,
                'message': 'Leave is already rejected'
            })

      
        leave.status = 'Rejected'
        if hasattr(leave, 'rejected_by'):
            leave.rejected_by = request.user
        if hasattr(leave, 'rejected_date'):
            leave.rejected_date = now()

       
        reason = data.get('reason', '')
        if reason:
            timestamp = now().strftime('%Y-%m-%d %H:%M')
            rejection_comment = f"\n\n[Rejected by {request.user.username} - {timestamp}]: {reason}"
            
            if leave.reason:
                leave.reason = f"{leave.reason}{rejection_comment}"
            else:
                leave.reason = f"[Rejected by {request.user.username} - {timestamp}]: {reason}"

        
        try:
            
            days_to_refund = 1.0 if leave.duration == 'full' else 0.5
            
           
            current_year = now().year
            
            leave_mapping = UserLeaveMapping.objects.filter(
                user_profile=leave.user_profile,
                leave_type=leave.leave_type,
                year=current_year,
                is_active=True
            ).first()
            
            if leave_mapping:
               
                leave_mapping.used_leaves -= days_to_refund
                leave_mapping.remaining_leaves += days_to_refund
                
               
                if leave_mapping.used_leaves < 0:
                    leave_mapping.used_leaves = 0.0
                
                
                if leave_mapping.remaining_leaves > leave_mapping.total_leaves:
                    leave_mapping.remaining_leaves = leave_mapping.total_leaves
                
                leave_mapping.row_modified_by = request.user.username
                leave_mapping.save()
                
                print(f"Refunded {days_to_refund} days to {leave.user_profile.username} for {leave.leave_type.name}. New balance: {leave_mapping.remaining_leaves}")
            else:
                print(f"No leave mapping found for {leave.user_profile.username} - {leave.leave_type.name} in {current_year}")
        
        except Exception as e:
            print(f"Error refunding leave balance: {str(e)}")

        leave.save()

        return JsonResponse({
            'success': True,
            'message': 'Leave rejected successfully',
            'new_status': 'Rejected',
            'leave_id': leave_id
        })

    except AppliedLeaves.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave not found or permission denied'
        })

    except Exception as e:
        print(f"Error rejecting leave {leave_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error rejecting leave: {str(e)}'
        })


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def add_leave_comment(request, leave_id):
    try:
        employee_ids = UserGroup.objects.filter(authority_user=request.user).values_list('emp_user_id', flat=True)
        
        data = {}
        if request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
        
        leave = AppliedLeaves.objects.get(
            id=leave_id,
            user_profile_id__in=employee_ids
        )
        
        new_comment = data.get('comment', '').strip()
        if not new_comment:
            return JsonResponse({'success': False, 'message': 'Comment cannot be empty'})
        
        timestamp = now().strftime('%Y-%m-%d %H:%M')
        admin_comment = f"\n\n[Admin Comment by {request.user.username} - {timestamp}]: {new_comment}"


        if leave.reason:
           leave.reason = f"{leave.reason}{admin_comment}"
        else:
           leave.reason = f"[Admin Comment by {request.user.username} - {timestamp}]: {new_comment}"

        leave.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Comment added successfully',
            'leave_id': leave_id
        })
    
    except AppliedLeaves.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Leave not found or you do not have permission'
        })
    except Exception as e:
        print(f"Error adding comment to leave {leave_id}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': f'Error adding comment: {str(e)}'
        })
    

@login_required
def leave_detail_ajax(request, leave_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        leave = get_object_or_404(AppliedLeaves, pk=leave_id)
        year = leave.leave_date.year
        leave_balance = get_leave_balance(leave.user_profile_id, leave.leave_type_id, year)
        
        data = {
            "success": True,
            "leave": {
                "employee": f"{leave.user_profile.first_name} {leave.user_profile.last_name}",
                "date": leave.leave_date.strftime('%Y-%m-%d'),
                "leave_type": leave.leave_type.name,
                "Duration": leave.duration,
                "leave_balance": leave_balance,
                "status": leave.status,
                "comments": leave.reason or ""
            }
        }
        return JsonResponse(data)
    return JsonResponse({"success": False}, status=400)

@csrf_exempt
@require_http_methods(["GET", "POST"])
@login_required
def edit_leave(request, leave_id):
    try:
        leave = AppliedLeaves.objects.get(id=leave_id)
    except AppliedLeaves.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Leave record not found'
        })

    if request.method == 'GET':
      
        leave_types = [
            {'id': lt.id, 'name': lt.name} 
            for lt in LeaveTypes.objects.filter(is_active=True)
        ]
        
      
        duration_choices = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in AppliedLeaves.DURATION_CHOICES
        ]
        
        
        status_choices = [
            {'value': choice[0], 'label': choice[1]}
            for choice in [('Pending', 'Pending'), ('Approved', 'Approved'),
                          ('Rejected', 'Rejected'), ('Cancelled', 'Cancelled')]
        ]
        
        return JsonResponse({
            'success': True,
            'leave': {
                'id': leave.id,
                'employee_name': leave.user_profile.username,
                'leave_type_id': leave.leave_type.id,
                'leave_type': leave.leave_type.name,
                'date': leave.leave_date.strftime('%Y-%m-%d'),
                'duration': leave.duration,
                'reason': leave.reason,
                'status': leave.status
            },
            'leave_types': leave_types,
            'duration_choices': duration_choices,
            'status_choices': status_choices
        })
    
    elif request.method == 'POST':
        try:
           
            import json
            from datetime import datetime
            data = json.loads(request.body)
            
          
            try:
                leave_type = LeaveTypes.objects.get(id=data.get('leave_type_id'))
            except LeaveTypes.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid leave type selected'
                })
            
           
            date_str = data.get('date')
            if date_str:
                try:
                   
                    leave_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid date format'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Date is required'
                })
            
          
            leave.leave_type = leave_type
            leave.leave_date = leave_date
            leave.duration = data.get('duration')
            leave.reason = data.get('reason')
            
          
            if data.get('status'):
                leave.status = data.get('status')
            
           
            leave.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Leave updated successfully',
                'leave': {
                    'id': leave.id,
                    'employee_name': leave.user_profile.username,
                    'leave_type': leave.leave_type.name,
                    'date': leave.leave_date.strftime('%Y-%m-%d'),
                    'duration': leave.duration,
                    'reason': leave.reason,
                    'status': leave.status
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating leave: {str(e)}'
            })
    
  
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    })