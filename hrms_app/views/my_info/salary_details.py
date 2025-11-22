from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from hrms_app.models import Salary

@login_required(login_url='/hrms_app/login/')
def salary_details_page(request):
    user = request.user
    all_salaries = Salary.objects.filter(user=user).order_by('-row_created_date')  # For table
    salary_details = all_salaries.first()  # Show latest data in form as default

    if request.method == 'POST':
        basic_salary = request.POST.get('basic_salary')
        hra = request.POST.get('hra')

        if basic_salary and hra:
            new_salary = Salary(
                user=user,
                basic_salary=Decimal(basic_salary),
                hra=Decimal(hra),
                special_allowance=Decimal(request.POST.get('special_allowance') or 0),
                bonus=Decimal(request.POST.get('bonus') or 0),
                other_allowances=Decimal(request.POST.get('other_allowances') or 0),
                deductions=Decimal(request.POST.get('deductions') or 0),
                net_salary=Decimal(request.POST.get('net_salary') or 0),
                payment_mode=request.POST.get('payment_mode') or 'bank_transfer',
                row_modified_by=user.username
            )
            new_salary.save()

            return redirect('salary_details_page')

    return render(request, 'my_info/salary_details.html', {
        'salary_details': salary_details,  # Show latest in form
        'all_salaries': all_salaries       # Table data
    })
