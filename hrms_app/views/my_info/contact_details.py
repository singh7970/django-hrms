from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from hrms_app.models.my_info.contact_details import ContactDetails

@login_required(login_url='/hrms_app/login/')
def contact_details_page(request):
    user = request.user
    contact, contact_detail = ContactDetails.objects.get_or_create(user=user)

    if request.method == 'POST':
        contact.street_1 = request.POST.get('street1')
        contact.street_2 = request.POST.get('street2')
        contact.city = request.POST.get('city')
        contact.state = request.POST.get('state')
        contact.postal_code = request.POST.get('postal_code')
        contact.country = request.POST.get('country')
        contact.home_phone = request.POST.get('home_phone')
        contact.mobile = request.POST.get('mobile')
        contact.work_phone = request.POST.get('work_phone')
        contact.work_email = request.POST.get('work_email')
        contact.other_email = request.POST.get('other_email')

        # Optionally track who made the changes
        contact.row_created_by = user.username
        contact.row_modified_by = user.username

        contact.save() 

        return redirect('contact_details_page')  

    return render(request, 'my_info/contact_details.html', {'contact': contact})
