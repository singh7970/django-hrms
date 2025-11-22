
from .views import roles
from .views import add_employee
from .views import holiday
from .views import employee_leaves
from .views import manage_leave
from .views import hr_dashboard
from .views import hr_my_info
from .views import directory
from .views import assign_leave
from .views.performance.my_reviews import my_reviews

from .views import leave_list
from .views.performance.add_emp_performance import add_employee_reviews
from .views.performance.employee_reviews import employee_reviews

from .views import entitlement
from .views import leave_type
from .views.my_info.dependents import dependents_page
from .views.my_info.job_details import job_details_page
from .views.my_info.Immigration_record import Immigration_page
from .views.my_info.contact_details import contact_details_page
from .views.my_info.salary_details import salary_details_page
from .views import time_attendance_records
from .views import time_punch_in_out_view
from django.urls import path
from .views import dashboard
from .views import time_dashboard

from .views import login_page
from .views import apply_leaves
from .views import my_leaves
from .views.my_info.personal_profile import show_personal_profile_page
from .views.my_info.emergency_contact import emergency_contact_page
from .views.performance.add_emp_performance import get_job_details, add_employee_reviews
from .views.performance.my_reviews import review_detail_view
from .views.performance.employee_reviews import employee_reviews

from .views.my_info.personal_documents import personal_documents_view
from .views.my_info.personal_documents import delete_personal_document
from .views.hr_attendance_management import hr_attendance_dashboard, edit_attendance_record, delete_attendance_record, create_attendance_record, attendance_analytics

from .views.leave_list import leave_detail_ajax



urlpatterns = [
    path('review-detail/<int:review_id>/', review_detail_view, name='review_detail'),
    path('performance/my_reviews', my_reviews, name='my_reviews'),
    path('get-job-details/',get_job_details,name="get_job_details"),    path('leave/details/<int:leave_id>/', leave_detail_ajax, name='leave_detail_ajax'),

    path('my_info/documents', personal_documents_view, name='personal_documents'),
    path('documents/delete/<int:doc_id>/', delete_personal_document, name='delete_personal_document'),
    path('performance/add_emp', add_employee_reviews, name='add_employee_reviews'),
    path('performance/emp_review', employee_reviews, name='employee_reviews'),
    path('my_info/salary_details/', salary_details_page, name='salary_details_page'),
    path('my_info/job_details/', job_details_page, name='job_details_page'),
    path('my_info/Immigration/', Immigration_page, name='Immigration_page'),
    path('my_info/dependents/', dependents_page, name='dependents_page'),
    path('my_info/emergency_contact/', emergency_contact_page, name='emergency_contact_page'),
    path('my_info/contact_details/', contact_details_page, name='contact_details_page'),
    path('my_info/personal_details/', show_personal_profile_page, name='show_personal_profile_page'),
    path('punch_in/', time_punch_in_out_view.save_punch_in_data, name='save_punch_in_data'),
    path('punch_out/', time_punch_in_out_view.save_punch_out_data, name='save_punch_out_data'),
    path('punchin_out_view/', time_punch_in_out_view.punch_in_out_page, name='punchin_out_view'),
    path('attendance_records/', time_attendance_records.attendance_records, name='attendance_records'),
    path('dashboard/', dashboard.show_dashboard_page, name='dashboard'),
    path('time_dashboard/', time_dashboard.time_dashboard_page, name='time_dashboard'),

    path("login/", login_page.show_login_page, name='login'),
    path("logout/", login_page.logout_view, name='logout'),
    path("apply_leave/", apply_leaves.apply_leave, name='apply_leaves'),
    path('get_leave_balance/', apply_leaves.get_leave_balance, name='get_leave_balance'),
    # path('my_leave/', apply_leaves.my_leave, name='my_leave'),
    path('my-leave/', my_leaves.my_leave, name='my_leave'),
    path('get-leave-details/', my_leaves.get_leave_details, name='get_leave_details'),
    path('cancel-leave/', my_leaves.cancel_leave, name='cancel_leave'),
    path('entitlements/',entitlement.leave_entitlements_view, name='entitlements'),
    path('api/leave-summary/',entitlement.get_leave_summary_api, name='leave_summary_api'),
    path('leave_list/',leave_list.leave_list_view, name='leave_list'),
      # path('leave/approve/<int:leave_id>/', leave_list.approve_leave, name='approve_leave'),
    # path('leave/reject/<int:leave_id>/', leave_list.reject_leave, name='reject_leave'),
    path('detail/<int:leave_id>/', leave_list.leave_detail_ajax, name='leave_detail_ajax'),
    path('approve-leave/<int:leave_id>/', leave_list.approve_leave, name='approve_leave'),
    path('reject-leave/<int:leave_id>/', leave_list.reject_leave, name='reject_leave'),
    path('edit-leave/<int:leave_id>/', leave_list.edit_leave, name='edit_leave'),
    path('add-leave-comment/<int:leave_id>/', leave_list.add_leave_comment, name='add_leave_comment'),
    path('assign_leave/', assign_leave.assign_leave, name='assign_leave'),
    path('api/get_leave_balance/', assign_leave.get_leave_balance, name='get_leave_balance_assign'),
   path('directory/', directory.employee_directory_view, name='directory'),
   path('api/employees/all/', directory.get_all_employees, name='get_all_employees'),
path('api/employees/search/', directory.search_employees, name='search_employees'),
path('api/employees/dropdown-options/', directory.get_dropdown_options, name='get_dropdown_options'),
path('hr-dashboard/main/', hr_dashboard.hr_main_dashboard, name='hr_dashboard_main'),
path('hr/manage-leaves/', manage_leave.manage_leaves, name='manage_leaves'),
path('hr/update-leave/', manage_leave.update_leave, name='update_leave'),
path('add-leave/', manage_leave.add_leave, name='add_leave'),
 path('leave-types/', leave_type.leave_types_page, name='leave_types_page'),
    path('leave-types/add/', leave_type.add_leave_type, name='add_leave_type'),
    path('leave-types/update/<int:id>/', leave_type.update_leave_type, name='update_leave_type'),
    path('leave-types/delete/<int:id>/', leave_type.delete_leave_type, name='delete_leave_type'),
     path('manage-leave-assignments/', employee_leaves.employee_leave_assignment_page, name='manage_leave_assignments'),
      path('api/get-leave-mapping/', employee_leaves.get_leave_mapping, name='get_leave_mapping'),
       path('api/update-leave-mapping/', employee_leaves.update_leave_mapping, name='update_leave_mapping'),
    path('api/add-leave-mapping/', employee_leaves.add_leave_mapping, name='add_leave_mapping'),
    # path('holidays/', holiday.holiday_page, name='holiday_page'),
    path('api/holidays/', holiday.HolidayAPIView.as_view(), name='holiday-list'),
    path('api/holidays/<int:pk>/', holiday.HolidayDetailAPIView.as_view(), name='holiday-detail'),

    path('holidays/', holiday.holiday_page, name='holiday_page'),
    path('employees/', add_employee.employee_management, name='employee_management'),
    path('employees/add/', add_employee.add_employee, name='add_employee'),
    path('employees/edit/<int:employee_id>/', add_employee.edit_employee, name='edit_employee'),
    path('employees/toggle-status/<int:employee_id>/', add_employee.toggle_employee_status, name='toggle_employee_status'),
    path('employees/delete/<int:employee_id>/', add_employee.delete_employee, name='delete_employee'),
    path('employees/toggle-superuser/<int:employee_id>/', add_employee.toggle_superuser_status, name='toggle_superuser_status'),
    path('employees/json/', add_employee.get_employees_json, name='get_employees_json'),
    path('roles/', roles.role_management_page, name='role-management'),
    
    # HR Attendance Management URLs
    path('hr/attendance/', hr_attendance_dashboard, name='hr_attendance_dashboard'),
    path('hr/attendance/edit/<int:record_id>/', edit_attendance_record, name='edit_attendance_record'),
    path('hr/attendance/delete/<int:record_id>/', delete_attendance_record, name='delete_attendance_record'),
    path('hr/attendance/create/', create_attendance_record, name='create_attendance_record'),
         path('hr/attendance/analytics/', attendance_analytics, name='attendance_analytics'),

     # HR Manage My Info
     path('hr/my-info/', hr_my_info.hr_manage_my_info, name='hr_manage_my_info'),
 ]
    # path('get_holiday_dates/', apply_leaves.get_holiday_dates, name='get_holiday_dates'),
