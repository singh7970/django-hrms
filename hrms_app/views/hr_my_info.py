from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hrms_app.models.users import UserProfile
from hrms_app.models.my_info.personal_details import PersonalDetails
from hrms_app.models.my_info.contact_details import ContactDetails
from hrms_app.models.my_info.emergency_contact import EmergencyContact
from hrms_app.models.my_info.dependents import Dependent
from hrms_app.models.my_info.job_details import JobDetails
from hrms_app.models.my_info.immigration import Immigration
from hrms_app.models.my_info.salary_details import Salary
from hrms_app.models.my_info.documents import PersonalDocument
from decimal import Decimal, InvalidOperation


def is_hr(user):
	try:
		return user.userrole.role.name.lower() == 'admin'
	except Exception:
		return False


@login_required(login_url='/hrms_app/login/')
def hr_manage_my_info(request):
	if not is_hr(request.user):
		messages.error(request, "You do not have permission to access this page.")
		return redirect('dashboard')

	employees = UserProfile.objects.filter(is_active=True).order_by('username')
	selected_user_id = request.POST.get('user_id') if request.method == 'POST' else request.GET.get('user_id')
	selected_user = UserProfile.objects.filter(id=selected_user_id).first() if selected_user_id else None

	personal_details = None
	contact_details = None
	emergency_contacts = []
	dependents = []
	job_details = None
	immigration_records = []
	salaries = []
	documents = []

	if selected_user:
		personal_details, _ = PersonalDetails.objects.get_or_create(user=selected_user)
		contact_details, _ = ContactDetails.objects.get_or_create(user=selected_user, defaults={
			'street_1': '', 'city': '', 'state': '', 'postal_code': '', 'country': '', 'mobile': '', 'work_email': selected_user.email or ''
		})
		emergency_contacts = list(EmergencyContact.objects.filter(user=selected_user).order_by('-row_created_date'))
		dependents = list(Dependent.objects.filter(user=selected_user).order_by('-row_created_date'))
		job_details, _ = JobDetails.objects.get_or_create(user=selected_user, defaults={
			'job_title': '', 'job_category': '', 'employment_status': 'full_time'
		})
		immigration_records = list(Immigration.objects.filter(user=selected_user).order_by('-row_created_date'))
		salaries = list(Salary.objects.filter(user=selected_user).order_by('-row_created_date'))
		documents = list(PersonalDocument.objects.filter(user=selected_user).order_by('-uploaded_at'))

	if request.method == 'POST' and selected_user:
		section = request.POST.get('section')
		try:
			if section == 'personal_details':
				# Update core user fields
				first_name = request.POST.get('first_name')
				last_name = request.POST.get('last_name')
				username = request.POST.get('username')
				dob = request.POST.get('dob')
				if first_name is not None:
					selected_user.first_name = first_name
				if last_name is not None:
					selected_user.last_name = last_name
				if username is not None and username.strip():
					selected_user.username = username.strip()
				if dob:
					selected_user.dob = dob
				selected_user.save()

				# Update personal details
				if personal_details:
					personal_details.middle_name = request.POST.get('middle_name') or None
					personal_details.other_id = request.POST.get('other_id') or None
					personal_details.license_number = request.POST.get('license_number') or None
					personal_details.license_expiry = request.POST.get('license_expiry') or None
					personal_details.nationality = request.POST.get('nationality') or None
					personal_details.marital_status = request.POST.get('marital_status') or None
					personal_details.gender = request.POST.get('gender') or None
					if request.FILES.get('attachment'):
						personal_details.attachment = request.FILES['attachment']
					personal_details.row_modified_by = request.user.username
					personal_details.save()
					messages.success(request, 'Personal details saved.')

			elif section == 'contact_details':
				if contact_details is None:
					contact_details = ContactDetails.objects.create(
						user=selected_user,
						street_1=request.POST.get('street_1') or '',
						street_2=request.POST.get('street_2') or '',
						city=request.POST.get('city') or '',
						state=request.POST.get('state') or '',
						postal_code=request.POST.get('postal_code') or '',
						country=request.POST.get('country') or '',
						home_phone=request.POST.get('home_phone') or '',
						mobile=request.POST.get('mobile') or '',
						work_phone=request.POST.get('work_phone') or '',
						work_email=request.POST.get('work_email') or '',
						other_email=request.POST.get('other_email') or '',
						row_created_by=request.user.username
					)
				else:
					contact_details.street_1 = request.POST.get('street_1') or ''
					contact_details.street_2 = request.POST.get('street_2') or ''
					contact_details.city = request.POST.get('city') or ''
					contact_details.state = request.POST.get('state') or ''
					contact_details.postal_code = request.POST.get('postal_code') or ''
					contact_details.country = request.POST.get('country') or ''
					contact_details.home_phone = request.POST.get('home_phone') or ''
					contact_details.mobile = request.POST.get('mobile') or ''
					contact_details.work_phone = request.POST.get('work_phone') or ''
					contact_details.work_email = request.POST.get('work_email') or ''
					contact_details.other_email = request.POST.get('other_email') or ''
					contact_details.row_modified_by = request.user.username
					contact_details.save()
				messages.success(request, 'Contact details saved.')

			elif section == 'emergency_contact_add':
				EmergencyContact.objects.create(
					user=selected_user,
					name=request.POST.get('name') or '',
					relationship=request.POST.get('relationship') or '',
					home_phone=request.POST.get('home_phone') or '',
					mobile=request.POST.get('mobile') or '',
					work_phone=request.POST.get('work_phone') or '',
					row_created_by=request.user.username
				)
				messages.success(request, 'Emergency contact added.')

			elif section == 'dependent_add':
				Dependent.objects.create(
					user=selected_user,
					name=request.POST.get('name') or '',
					relationship=request.POST.get('relationship') or 'other',
					dob=request.POST.get('dob') or None,
					row_created_by=request.user.username
				)
				messages.success(request, 'Dependent added.')

			elif section == 'job_details':
				if job_details is None:
					job_details = JobDetails.objects.create(
						user=selected_user,
						job_title=request.POST.get('job_title') or '',
						job_category=request.POST.get('job_category') or '',
						sub_unit=request.POST.get('sub_unit') or None,
						location=request.POST.get('location') or None,
						job_specification=request.POST.get('job_specification') or None,
						employment_status=request.POST.get('employment_status') or 'full_time',
						row_created_by=request.user.username
					)
				else:
					job_details.job_title = request.POST.get('job_title') or ''
					job_details.job_category = request.POST.get('job_category') or ''
					job_details.sub_unit = request.POST.get('sub_unit') or None
					job_details.location = request.POST.get('location') or None
					job_details.job_specification = request.POST.get('job_specification') or None
					job_details.employment_status = request.POST.get('employment_status') or 'full_time'
					job_details.row_modified_by = request.user.username
					job_details.save()
				messages.success(request, 'Job details saved.')

			elif section == 'immigration_add':
				Immigration.objects.create(
					user=selected_user,
					document_type=request.POST.get('document_type') or 'passport',
					number=request.POST.get('number') or '',
					issued_date=request.POST.get('issued_date') or None,
					expiry_date=request.POST.get('expiry_date') or None,
					eligible_state=request.POST.get('eligible_state') or '',
					issued_by=request.POST.get('issued_by') or 'india',
					eligible_review_date=request.POST.get('eligible_review_date') or None,
					comment=request.POST.get('comment') or None,
					row_created_by=request.user.username
				)
				messages.success(request, 'Immigration record added.')

			elif section == 'salary_add':
				def d(key):
					val = request.POST.get(key)
					try:
						return Decimal(val) if val not in [None, ''] else None
					except InvalidOperation:
						return None
				Salary.objects.create(
					user=selected_user,
					basic_salary=d('basic_salary') or Decimal('0.00'),
					hra=d('hra') or Decimal('0.00'),
					special_allowance=d('special_allowance'),
					bonus=d('bonus'),
					other_allowances=d('other_allowances'),
					deductions=d('deductions'),
					net_salary=d('net_salary'),
					payment_mode=request.POST.get('payment_mode') or 'bank_transfer',
					row_created_by=request.user.username
				)
				messages.success(request, 'Salary record added.')

			elif section == 'document_add':
				doc_type = request.POST.get('document_type') or 'other'
				file_obj = request.FILES.get('document_file')
				if not file_obj:
					messages.error(request, 'Please select a file to upload.')
				else:
					# update if exists, else create
					obj, created = PersonalDocument.objects.get_or_create(user=selected_user, document_type=doc_type, defaults={
						'document_file': file_obj,
						'row_created_by': request.user.username
					})
					if not created:
						obj.document_file = file_obj
						obj.row_modified_by = request.user.username
						obj.save()
					messages.success(request, 'Document uploaded.')

			# redirect to preserve selected employee in query
			return redirect(f"/hrms_app/hr/my-info/?user_id={selected_user.pk}")

		except Exception as e:
			messages.error(request, f"Error: {e}")
			return redirect('hr_manage_my_info')

	return render(request, 'hr_dashboard/hr_manage_my_info.html', {
		'employees': employees,
		'selected_user': selected_user,
		'personal_details': personal_details,
		'contact_details': contact_details,
		'emergency_contacts': emergency_contacts,
		'dependents': dependents,
		'job_details': job_details,
		'immigration_records': immigration_records,
		'salaries': salaries,
		'documents': documents,
	}) 