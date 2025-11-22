from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.db.models import Q
import json
from datetime import date
from ..models import UserProfile

@login_required
def employee_management(request):
    """Display employee management page"""
    search_query = request.GET.get('search', '')
    
    # Filter employees based on search - order by latest first
    employees = UserProfile.objects.all().order_by('-date_joined')
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Pagination - 5 employees per page
    paginator = Paginator(employees, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'employees': page_obj,
        'search_query': search_query,
        'total_employees': UserProfile.objects.count(),
        'active_employees': UserProfile.objects.filter(is_active=True).count(),
        'inactive_employees': UserProfile.objects.filter(is_active=False).count(),
        'superuser_employees': UserProfile.objects.filter(is_superuser=True).count(),
    }
    return render(request, 'add_employee.html', context)

@login_required
@csrf_exempt
def add_employee(request):
    """Add new employee via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Check if email already exists
            if UserProfile.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Employee with this email already exists.'
                })
            
            # Check if username already exists
            if UserProfile.objects.filter(username=data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Employee with this username already exists.'
                })
            
            # Create new employee
            employee = UserProfile.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                username=data['username'],
                email=data['email'],
                password=make_password(data['password']),
                is_active=data.get('is_active', True),
                is_superuser=data.get('is_superuser', False),
                is_staff=data.get('is_superuser', False),  # Staff status for admin access
                row_created_by=request.user.username if hasattr(request.user, 'username') else 'system',
                row_modified_by=request.user.username if hasattr(request.user, 'username') else 'system'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Employee {"and Superuser" if data.get("is_superuser") else ""} added successfully!',
                'employee': {
                    'id': employee.id,
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'username': employee.username,
                    'email': employee.email,
                    'date_joined': employee.date_joined.strftime('%Y-%m-%d') if employee.date_joined else '',
                    'is_active': employee.is_active,
                    'is_superuser': employee.is_superuser
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def edit_employee(request, employee_id):
    """Edit employee via AJAX"""
    if request.method == 'POST':
        try:
            employee = get_object_or_404(UserProfile, id=employee_id)
            data = json.loads(request.body)
            
            # Check if email already exists (excluding current employee)
            if UserProfile.objects.filter(email=data['email']).exclude(id=employee_id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Employee with this email already exists.'
                })
            
            # Check if username already exists (excluding current employee)
            if UserProfile.objects.filter(username=data['username']).exclude(id=employee_id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Employee with this username already exists.'
                })
            
            # Update employee
            employee.first_name = data['first_name']
            employee.last_name = data['last_name']
            employee.username = data['username']
            employee.email = data['email']
            employee.is_active = data.get('is_active', employee.is_active)
            employee.is_superuser = data.get('is_superuser', employee.is_superuser)
            employee.is_staff = data.get('is_superuser', employee.is_superuser)  # Staff status for admin access
            employee.row_modified_by = request.user.username if hasattr(request.user, 'username') else 'system'
            
            # Update password if provided
            if data.get('password'):
                employee.password = make_password(data['password'])
            
            employee.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Employee updated successfully! {"Superuser privileges granted." if data.get("is_superuser") else ""}',
                'employee': {
                    'id': employee.id,
                    'first_name': employee.first_name,
                    'last_name': employee.last_name,
                    'username': employee.username,
                    'email': employee.email,
                    'date_joined': employee.date_joined.strftime('%Y-%m-%d') if employee.date_joined else '',
                    'is_active': employee.is_active,
                    'is_superuser': employee.is_superuser
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    elif request.method == 'GET':
        # Get employee data for editing
        employee = get_object_or_404(UserProfile, id=employee_id)
        return JsonResponse({
            'success': True,
            'employee': {
                'id': employee.id,
                'first_name': employee.first_name,
                'last_name': employee.last_name,
                'username': employee.username,
                'email': employee.email,
                'date_joined': employee.date_joined.strftime('%Y-%m-%d') if employee.date_joined else '',
                'is_active': employee.is_active,
                'is_superuser': employee.is_superuser
            }
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def toggle_employee_status(request, employee_id):
    """Toggle employee active/inactive status"""
    if request.method == 'POST':
        try:
            employee = get_object_or_404(UserProfile, id=employee_id)
            employee.is_active = not employee.is_active
            employee.row_modified_by = request.user.username
            employee.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Employee {"activated" if employee.is_active else "deactivated"} successfully!',
                'is_active': employee.is_active
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def delete_employee(request, employee_id):
    """Delete employee - Enhanced with safety checks"""
    if request.method == 'DELETE':
        try:
            employee = get_object_or_404(UserProfile, id=employee_id)
            employee_name = f"{employee.first_name} {employee.last_name}"
            
            # Safety check: Don't allow deleting the current user
            if employee.id == request.user.id:
                return JsonResponse({
                    'success': False,
                    'error': 'You cannot delete your own account!'
                })
            
            # Safety check: Don't allow deleting the last superuser
            if employee.is_superuser and UserProfile.objects.filter(is_superuser=True).count() <= 1:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete the last superuser account!'
                })
            
            # Log the deletion
            deleted_employee_info = {
                'id': employee.id,
                'name': employee_name,
                'email': employee.email,
                'was_superuser': employee.is_superuser,
                'deleted_by': request.user.username if hasattr(request.user, 'username') else 'system'
            }
            
            employee.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Employee "{employee_name}" has been permanently deleted.',
                'deleted_employee': deleted_employee_info
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error deleting employee: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def toggle_superuser_status(request, employee_id):
    """Toggle employee superuser status - Separate endpoint for security"""
    if request.method == 'POST':
        try:
            # Only superusers can change superuser status
            if not request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'error': 'Only superusers can grant/revoke superuser privileges.'
                })
            
            employee = get_object_or_404(UserProfile, id=employee_id)
            
            # Safety check: Don't allow removing superuser from the current user
            if employee.id == request.user.id and employee.is_superuser:
                return JsonResponse({
                    'success': False,
                    'error': 'You cannot remove superuser privileges from your own account!'
                })
            
            # Safety check: Don't allow removing the last superuser
            if employee.is_superuser and UserProfile.objects.filter(is_superuser=True).count() <= 1:
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot remove superuser privileges from the last superuser account!'
                })
            
            # Toggle superuser status
            employee.is_superuser = not employee.is_superuser
            employee.is_staff = employee.is_superuser  # Staff status for admin access
            employee.row_modified_by = request.user.username
            employee.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Superuser privileges {"granted to" if employee.is_superuser else "revoked from"} {employee.first_name} {employee.last_name}!',
                'is_superuser': employee.is_superuser
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_employees_json(request):
    """Get all employees as JSON for frontend"""
    search_query = request.GET.get('search', '')
    
    employees = UserProfile.objects.all()
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    employees_data = []
    for employee in employees:
        employees_data.append({
            'id': employee.id,
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'username': employee.username,
            'email': employee.email,
            'date_joined': employee.date_joined.strftime('%Y-%m-%d') if employee.date_joined else '',
            'is_active': employee.is_active,
            'is_superuser': employee.is_superuser,
            'is_staff': employee.is_staff,
            'row_created_date': employee.row_created_date.strftime('%Y-%m-%d %H:%M:%S') if employee.row_created_date else '',
            'row_created_by': employee.row_created_by,
            'row_modified_by': employee.row_modified_by
        })
    
    return JsonResponse({
        'success': True,
        'employees': employees_data,
        'total': len(employees_data),
        'stats': {
            'total_employees': UserProfile.objects.count(),
            'active_employees': UserProfile.objects.filter(is_active=True).count(),
            'inactive_employees': UserProfile.objects.filter(is_active=False).count(),
            'superuser_employees': UserProfile.objects.filter(is_superuser=True).count(),
        }
    })