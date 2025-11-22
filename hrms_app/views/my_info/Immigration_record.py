from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from hrms_app.models.my_info.immigration import Immigration


@login_required(login_url='/hrms_app/login/')
def Immigration_page(request):
    user_profile = request.user 
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        number = request.POST.get('number')
        issued_date = request.POST.get('issued_date')
        expiry_date = request.POST.get('expiry_date')
        eligible_state = request.POST.get('eligible_state')
        issued_by = request.POST.get('issued_by')

        eligible_review_date = request.POST.get('eligible_review_date')or None
        comment = request.POST.get('comment')

      

    
        Immigration.objects.create(
            user=user_profile,
            document_type=document_type,
            number=number,
            issued_date=issued_date,
            expiry_date=expiry_date,
            eligible_state=eligible_state,
            issued_by=issued_by,
            eligible_review_date=eligible_review_date or None,
            comment=comment,
            row_created_by=request.user.username,
            row_modified_by=request.user.username,
        )
        return redirect("Immigration_page")
    data = Immigration.objects.filter(user=user_profile).order_by('-issued_date')
    return render(request, 'my_info/Immigration.html', {
        'data': data
    })
