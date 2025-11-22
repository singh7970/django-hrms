from django.contrib.auth.decorators import login_required
from django.shortcuts import render ,redirect
from hrms_app.models.my_info.personal_details import PersonalDetails

@login_required(login_url='/hrms_app/login/')
def show_personal_profile_page(request):
    user = request.user
    personal_details, _ = PersonalDetails.objects.get_or_create(user=user)
   
    if request.method == 'POST':
        # Get data from the form
        other_id = request.POST.get('otherID')
        license_number = request.POST.get('licenseNumber')
        license_expiry = request.POST.get('licenseExpiry')
        nationality = request.POST.get('nationality')
        marital_Status = request.POST.get('marital_Status')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob') 
        middle_name = request.POST.get('middleName')
        
        
        # Save data into the model
        personal_details.other_id = other_id
        personal_details.license_number = license_number
        personal_details.license_expiry = license_expiry or None
        personal_details.nationality = nationality
        personal_details.marital_status = marital_Status
        personal_details.gender = gender

        # Optional: save middle name or dob to `User` or extended profile
        if middle_name:
            user.middle_name = middle_name  # Only if you have this field
        if dob:
            user.dob = dob  # Only if you have this field in User model
        user.save()
        personal_details.save()

        # Optional success message
        

        return redirect('show_personal_profile_page')  # Redirect to avoid form resubmission

    return render(request, 'my_info/perosnal_prof.html', {
        'user': user,
        'personal_details': personal_details
    })