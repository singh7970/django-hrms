from hrms_app.models.my_info.immigration import Immigration
from hrms_app.models.performance.user_group import UserGroup
from hrms_app.models.performance.emp_review_details import EmployeeReview
from hrms_app.models.my_info.salary_details import Salary
from hrms_app.models.time_attendance_record import AttendanceRecord
from hrms_app.models.my_info.emergency_contact import EmergencyContact
from hrms_app.models.my_info.job_details import JobDetails
from hrms_app.models.my_info.dependents import Dependent
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from hrms_app.models.users import UserProfile
from hrms_app.models.applied_leaves import AppliedLeaves
from hrms_app.models.leave_types import LeaveTypes
from hrms_app.models.user_leave_mapping import UserLeaveMapping
from hrms_app.models.holiday import Holiday
from hrms_app.models.my_info.personal_details import PersonalDetails
from hrms_app.models.my_info.contact_details import ContactDetails
from hrms_app.models.role import Role
from hrms_app.models.permission import Permission
from hrms_app.models.role_permission import RolePermission
from hrms_app.models.user_role import UserRole
from hrms_app.models.my_info.documents import PersonalDocument

# Register your models here.

class UserProfileAdmin(UserAdmin):
    pass

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(LeaveTypes)

# class UserLeaveMappingAdmin(admin.ModelAdmin):
#     def save_model(self, request, obj, form, change):
#         if not obj.pk:
#             obj.row_created_by = request.user
#         obj.row_modified_by = request.user
#         super().save_model(request, obj, form, change)

admin.site.register(UserLeaveMapping)
# admin.site.register(AppliedLeaveDates)

# class AppliedLeavesAdmin(admin.ModelAdmin):
#     list_display = ('user', 'leave_type', 'start_date', 'end_date', 'status')
#     list_filter = ('status', 'leave_type')
#     search_fields = ('user__username', 'leave_type__name')

#     def save_model(self, request, obj, form, change):
#         previous_status = None
#         if obj.pk:
#             previous_status = AppliedLeaves.objects.get(pk=obj.pk).status

#         super().save_model(request, obj, form, change)

#         # Only update if status changed to Approved
#         if obj.status == "Approved" and previous_status != "Approved":
#             leave_days = (obj.end_date - obj.start_date).days + 1

#             leave_balance = UserLeaveMapping.objects.filter(
#                 user=obj.user,
#                 leave_type=obj.leave_type,
#                 is_active=True
#             ).first()

#             if leave_balance and leave_balance.remaining_leaves >= leave_days:
#                 leave_balance.used_leaves += leave_days
#                 leave_balance.remaining_leaves = leave_balance.total_leaves - leave_balance.used_leaves
#                 leave_balance.save()
#             else:
#                 # Optional: Rollback approval or notify if insufficient balance
#                 pass

admin.site.register(Permission) 
admin.site.register(PersonalDocument) 

# admin.site.register(UserGroup) 
admin.site.register(Role) 
admin.site.register(UserRole) 
admin.site.register(RolePermission) 
admin.site.register(EmployeeReview) 
admin.site.register(JobDetails)
admin.site.register(Salary)
admin.site.register(Immigration)
admin.site.register(Dependent)
admin.site.register(EmergencyContact)
admin.site.register(ContactDetails)
admin.site.register(PersonalDetails)
admin.site.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'punch_in_time', 'punch_out_time', 'duration_hms', 'status')

    def duration_hms(self, obj):
        return obj.duration_hms()
    duration_hms.short_description = 'Duration (H:M:S)'

# admin.site.register(AppliedLeaves)

def approve_leaves(modeladmin, request, queryset):
    queryset.update(status='Approved')

def reject_leaves(modeladmin, request, queryset):
    for leave in queryset:
        if leave.status != 'Rejected':
            # Convert duration to float value
            if leave.duration == 'full':
                leave_days = 1.0
            elif leave.duration in ['half_morning', 'half_evening']:
                leave_days = 0.5
            else:
                leave_days = 0.0  # Fallback, in case duration is invalid

            # Fetch UserLeaveMapping for this user and leave type for current year
            try:
                mapping = UserLeaveMapping.objects.get(
                    user_profile=leave.user_profile,
                    leave_type=leave.leave_type,
                    year=leave.leave_date.year,
                    is_active=True
                )

                # Revert leave balance
                mapping.used_leaves = max(mapping.used_leaves - leave_days, 0)
                mapping.remaining_leaves = mapping.total_leaves - mapping.used_leaves
                mapping.save()
            except UserLeaveMapping.DoesNotExist:
                # Handle missing mapping gracefully
                pass

            # Update leave status
            leave.status = 'Rejected'
            leave.save()
    
class AppliedLeavesAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'leave_type', 'leave_date', 'duration', 'status', 'row_create_date')
    list_filter = ('leave_type', 'status')
    search_fields = ('user_profile__username', 'leave_type__name')
    list_display_links = ('status',)
    actions = [approve_leaves, reject_leaves]

    

admin.site.register(AppliedLeaves, AppliedLeavesAdmin)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'occasion')
    ordering = ('date',)

from django.contrib import admin
from hrms_app.models import UserGroup, UserProfile

@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('emp_user', 'authority_user', 'row_created_date')
    search_fields = ('emp_user__email', 'authority_user__email')
    list_filter = ('authority_user',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "authority_user":
            kwargs["queryset"] = UserProfile.objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
