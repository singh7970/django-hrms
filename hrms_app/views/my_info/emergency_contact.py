from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from hrms_app.models.my_info.emergency_contact import EmergencyContact

@login_required(login_url='/hrms_app/login/')
def emergency_contact_page(request):
    user_profile = request.user 

    if request.method == 'POST':
        name = request.POST.get('name')
        relationship = request.POST.get('relationship')
        home_phone = request.POST.get('home_phone')
        mobile = request.POST.get('mobile')
        work_phone = request.POST.get('work_phone')

        

        EmergencyContact.objects.create(
            user=user_profile,
            name=name,
            relationship=relationship,
            home_phone=home_phone,
            mobile=mobile,
            work_phone=work_phone,
            row_created_by=request.user.username
        )
        print(name,relationship,home_phone,work_phone,mobile)
        return redirect('emergency_contact_page')  # reload page to show new contact

    # For GET request, fetch all emergency contacts
    contacts = EmergencyContact.objects.filter(user=user_profile)

    return render(request,'my_info/emergency_contact.html', {
        'contacts': contacts
    })
