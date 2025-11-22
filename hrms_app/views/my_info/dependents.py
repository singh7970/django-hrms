from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from hrms_app.models.my_info.dependents import Dependent

from hrms_app.models import UserProfile

@login_required(login_url='/hrms_app/login/')
def dependents_page(request):
    user_profile = request.user     

    if request.method == 'POST':
        name = request.POST.get('name')
        relationship = request.POST.get('relationship')
        dob = request.POST.get('dob')

        
        print(name,relationship,dob)
        Dependent.objects.create(
            user=user_profile,
            name=name,
            relationship=relationship,
            dob=dob,
            row_created_by=request.user.username
        )
        return redirect('dependents_page')  # Update with your actual URL name

    dependents = Dependent.objects.filter(user=user_profile)
    return render(request, 'my_info/dependents.html', {
        'dependents': dependents
    })
