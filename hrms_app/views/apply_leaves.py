from datetime import date, datetime, timedelta
import inspect

from django.shortcuts import redirect, render
from django.contrib import messages

from hrms_app.models.holiday import Holiday
from ..models.user_leave_mapping import UserLeaveMapping
from ..models.applied_leaves import  AppliedLeaves
from ..models.leave_types import LeaveTypes
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required 
from ..models.users import UserProfile








SL = "SL"
CL = "CL"
WFH = "WFH"


LEAVE_QUOTA = {
    'CL': 10,   
    'SL': 5,    
    'PL': 8,    
    'LWP': 0,   
    'WFH': 3,   
}
@login_required(login_url='/hrms_app/login/')
def show_apply_leaves(request):
    leave_types = LeaveTypes.objects.all(is_active=True)  # Fetch all leave types from DB
    return render(request, 'apply_leave.html', {'leave_types': leave_types})

@login_required(login_url='/hrms_app/login/')
def initialize_leave_for_new_year(request):
    
    new_year = datetime.today().year

   
    UserLeaveMapping.objects.filter(year__lt=new_year, is_active=True).update(is_active=False)

    users = UserProfile.objects.all()
    leave_types = LeaveTypes.objects.all()

    for user in users:
        for leave_type in leave_types:
            code = leave_type.name  
            if code in LEAVE_QUOTA:
                total = LEAVE_QUOTA[code]
                UserLeaveMapping.objects.create(
                    user_profile=user,
                    leave_type=leave_type,
                    total_leaves=total,
                    used_leaves=0,
                    remaining_leaves=total,
                    year=new_year,
                    is_active=True,
                    row_created_by='system',
                    row_modified_by='system',
                )
    return HttpResponse("Leave mappings for new year created.")
@login_required(login_url='/hrms_app/login/')
def get_available_leaves(request):
    user_profile = UserProfile.objects.get(user=request.user)
    available_leaves = UserLeaveMapping.objects.filter(user_profile=user_profile, is_active=True)
    return render(request, 'apply_leave.html', {'available_leaves': available_leaves})




@login_required(login_url='/hrms_app/login/')
def apply_leave(request):
    user_profile = request.user

    if request.method == "POST":
        leave_type_id = request.POST.get("leave_type")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason", "")
        duration = request.POST.get("duration", "")
        print("duration", duration)
        

        is_half_day = False
        if duration in ('half_evening', 'half_morning'):
            is_half_day = True

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('apply_leaves')

        if end_date_obj < start_date_obj:
            messages.error(request, "End date cannot be before start date.")
            return redirect('apply_leaves')

        try:
            leave_type = LeaveTypes.objects.get(id=leave_type_id)
        except LeaveTypes.DoesNotExist:
            messages.error(request, "Invalid leave type.")
            return redirect('apply_leaves')

        total_days = 0
        leave_dates = []
        current_date = start_date_obj

        while current_date <= end_date_obj:
            date_str = current_date.strftime("%Y-%m-%d")
            leave_day_type = request.POST.get(f"duration_{date_str}", duration)

            # Skip weekends and holidays for sick leave and WFH
            if leave_type.code.upper() in [SL, WFH] and (current_date.weekday() in [5, 6] or 
                Holiday.objects.filter(date=current_date).exists()):
                print(f"Skipping weekend {date_str} for {leave_type.name}")
                current_date += timedelta(days=1)
                continue

          

            leave_dates.append((current_date, leave_day_type))
            print(f"Date: {date_str}, Selected duration: {leave_day_type}")

            if leave_day_type in ['half_morning', 'half_evening']:
                total_days += 0.5
                print(f"Added 0.5 day for {date_str}. Total so far: {total_days}")
            else:
                total_days += 1
                print(f"Added 1 day for {date_str}. Total so far: {total_days}")

            current_date += timedelta(days=1)

        # Check if there are enough leaves
        leave_balance = UserLeaveMapping.objects.filter(
            user_profile=user_profile,
            leave_type=leave_type,
            is_active=True
        ).first()

        if not leave_balance or leave_balance.remaining_leaves < total_days:
            messages.error(request, "You do not have enough leave balance for this type.")
            return redirect('apply_leaves')

        # Check if the user has already applied leave for any of these dates
        existing_leaves = AppliedLeaves.objects.filter(
            user_profile=user_profile,
            leave_date__range=[start_date_obj, end_date_obj]
        ).exclude(
    
    status__in=['Cancelled', 'Rejected'])    
        if existing_leaves.exists():
            messages.error(request, "You have already applied leave for one or more of these dates.")
            return redirect('apply_leaves')
           
        
        
        # Handle sandwich leave conflicts
        conflict_message = is_sandwich_conflict(user_profile, leave_dates, leave_type)
        if conflict_message:
            messages.error(request, conflict_message)
            return redirect('apply_leaves')

        

        
        
        # Deduct the leave days from the balance and save it
        for date, day_type in leave_dates:

            AppliedLeaves.objects.create(
                user_profile=user_profile,
                leave_type=leave_type,
                leave_date=date,
                reason=reason,
                duration=day_type,
                status="Pending",
            )

            
            flag, leave_list = previous_leave_deductions(date,user_profile)
            print(flag, leave_list)
            if flag:
               for day in leave_list:
                  deducted_flag = create_auto_leave_entry(user_profile, day)
                  print("deducted_flag",deducted_flag)
       
        

        # Update the leave balance after applying the leave
        leave_balance = UserLeaveMapping.objects.get(user_profile=user_profile, leave_type=leave_type)
        leave_balance.used_leaves += total_days
        leave_balance.remaining_leaves -= total_days
        leave_balance.remaining_leaves = max(0, leave_balance.remaining_leaves)
        leave_balance.save()

        combined_sandwich_handler(user_profile, leave_dates, leave_type)
        # '''
        # Set success message and redirect
        request.session['success_flag'] = True
        return redirect('apply_leaves')

    # GET request
    success_flag = request.session.pop('success_flag', False)
    return render(request, "apply_leave.html", {
        "leave_types": LeaveTypes.objects.filter(is_active=True),
        "success_flag": success_flag
    })
 

@login_required
def get_leave_balance(request):
    leave_type_id = request.GET.get("leave_type_id")
    if not leave_type_id:
        return JsonResponse({"error": "Leave type ID not provided"}, status=400)

    try:
        leave_type = LeaveTypes.objects.get(id=leave_type_id)
        mapping = UserLeaveMapping.objects.filter(
            user_profile=request.user,
            leave_type=leave_type,
            is_active=True
        ).first()

        if mapping:
            return JsonResponse({"balance": float(mapping.remaining_leaves)})
        else:
            return JsonResponse({"balance": 0})
    except LeaveTypes.DoesNotExist:
        return JsonResponse({"error": "Invalid leave type"}, status=404)
# def my_leave(request):
#     return render(request, 'my_leave.html')

def is_sandwich_conflict(user, leave_dates, current_leave_type):
    applied_dates = {ld[0] for ld in leave_dates}
    leave_type_name = current_leave_type.name.lower()
    holidays = set(Holiday.objects.values_list("date", flat=True))  # Assume this returns a set of holiday dates

    for date in applied_dates:
        prev_prev_day = date - timedelta(days=2)
        prev_day = date - timedelta(days=1)
        next_day = date + timedelta(days=1)

        prev_leave = AppliedLeaves.objects.filter(
            user_profile=user,
            leave_date=prev_day,
            is_active=True,
            status__in=["Pending", "Approved"]
        ).first()

        next_leave = AppliedLeaves.objects.filter(
            user_profile=user,
            leave_date=next_day,
            is_active=True,
            status__in=["Pending", "Approved"]
        ).first()

        prev_prev_leave = AppliedLeaves.objects.filter(
            user_profile=user,
            leave_date=prev_prev_day,
            is_active=True,
            status__in=["Pending", "Approved"]
        ).first()

        # CASE 1: Applying SL between two CL/PL
        if leave_type_name == 'sick leave':
            if prev_leave and next_leave:
                if prev_leave.leave_type.name.lower() in ['casual leave', 'priviledge leave'] and \
                   next_leave.leave_type.name.lower() in ['casual leave', 'priviledge leave'] or \
                   prev_prev_leave and prev_prev_leave.leave_type.name.lower() == 'sick leave' and \
                   prev_leave.leave_type.name.lower() in ['casual leave', 'priviledge leave']:
                    return "You cannot take Sick Leave between two Casual/priviledge leaves."

        # CASE 2: SL already applied and user is trying to apply CL/PL
        if leave_type_name in ['casual leave', 'priviledge leave']:
            if (prev_leave and prev_leave.leave_type.name.lower() == 'sick leave') and \
               (next_leave and next_leave.leave_type.name.lower() == 'sick leave') or \
               (prev_prev_leave and prev_prev_leave.leave_type.name.lower() in ['casual leave', 'priviledge leave']) and \
               (prev_leave and prev_leave.leave_type.name.lower() == 'sick leave'):
                return "You cannot take Casual/priviledge leave adjacent to an existing Sick Leave." 

        # CASE 3: SL before and CL/PL/LWP after (or vice versa) around weekend/holiday 
        for offset in range(-3, 4):  # Check 3 days around
            middle_day = date + timedelta(days=offset)
            if middle_day.weekday() in [5, 6] or middle_day in holidays:
                before_day = middle_day - timedelta(days=1)
                after_day = middle_day + timedelta(days=1)

                before_leave = AppliedLeaves.objects.filter(
                    user_profile=user,
                    leave_date=before_day,
                    is_active=True,
                    status__in=["Pending", "Approved"]
                ).first()

                after_leave = AppliedLeaves.objects.filter(
                    user_profile=user,
                    leave_date=after_day,
                    is_active=True,
                    status__in=["Pending", "Approved"]
                ).first()

                if before_leave and after_leave:
                    before_type = before_leave.leave_type.name.lower()
                    after_type = after_leave.leave_type.name.lower()

                    valid = (
                        (before_type == 'sick leave' and after_type in ['casual leave', 'priviledge leave', 'lwp']) or
                        (after_type == 'sick leave' and before_type in ['casual leave', 'priviledge leave', 'lwp'])
                    )

                    if valid:
                        already_exists = AppliedLeaves.objects.filter(
                            user_profile=user,
                            leave_date=middle_day,
                            is_active=True
                        ).exists()

                        if not already_exists:
                            create_auto_leave_entry(user, middle_day)  # 🛠 Create leave for weekend/holiday

    return None


def create_auto_leave_entry(user_profile, day):
    print("Day ----------", day)

    # Identify the function that called this
    caller_function = inspect.stack()[1].function
    print(f"create_auto_leave_entry called from: {caller_function}")

    # Define leave type priority
    priority_order = ['casual leave', 'priviledge leave', 'sick leave', 'leave without pay']

    for leave_name in priority_order:
        leave_type = LeaveTypes.objects.filter(name__iexact=leave_name).first()
        if not leave_type:
            print(f"[Skip] LeaveType not found: {leave_name}")
            continue

        leave_map = UserLeaveMapping.objects.filter(
            user_profile=user_profile,
            leave_type=leave_type,
            is_active=True
        ).first()

        if not leave_map:
            print(f"[Skip] No leave mapping found for {leave_name} and user {user_profile}")
            continue

        print(f"[Check] {leave_name.capitalize()} Leave - Remaining: {leave_map.remaining_leaves}")

        # Check balance
        if leave_map.remaining_leaves >= 1:
            # Check for existing leave entry
            leave_exists = AppliedLeaves.objects.filter(
                user_profile=user_profile,
                leave_date=day,
                leave_type=leave_type
            ).exists()

            if leave_exists:
                print(f"[Info] Leave already exists on {day} for {leave_name}")
            else:
                # Create leave entry
                AppliedLeaves.objects.create(
                    user_profile=user_profile,
                    leave_type=leave_type,
                    leave_date=day,
                    reason="Weekend Sandwich Deduction",
                    duration="full",
                    status="Auto-Approved"
                )
                print(f"[Success] Created auto leave on {day} for {leave_name}")
                leave_map.refresh_from_db()
            # Deduct leave balance (only once even if leave already exists)
                before = leave_map.remaining_leaves
                leave_map.used_leaves += 1
                leave_map.remaining_leaves -= 1
                leave_map.remaining_leaves = max(0, leave_map.remaining_leaves)
                leave_map.save()

                print(f"[Deducted] 1 day from {leave_name}. Before: {before}, After: {leave_map.remaining_leaves}")
                return True

        else:
            print(f"[Skip] Not enough balance in {leave_name}")

    print("[Fail] No sufficient leave balance found for any leave type.")
    return False




def is_leave_day(user_profile, date):
    return AppliedLeaves.objects.filter(user_profile=user_profile, leave_date=date).exists()

def has_no_working_gap(user_profile, start_date, end_date):
    """Return True if all days between start and end are leave days (no working day in between)."""
    current = start_date + timedelta(days=1)
    while current < end_date:
        if not is_leave_day(user_profile, current):
            return False
        current += timedelta(days=1)
    return True

def has_continuous_cl_pl_lwp(user_profile, start_date, direction='backward'):
    """Check if there are 2+ continuous CL/PL/LWP in the given direction from the start_date."""
    count = 0
    date = start_date

    while True:
        date = date - timedelta(days=1) if direction == 'backward' else date + timedelta(days=1)
        leave = AppliedLeaves.objects.filter(user_profile=user_profile, leave_date=date).first()

        if not leave:
            break
        if leave.leave_type.code.upper() in ['CL', 'PL', 'LWP']:
            count += 1
        else:
            break

        if count >= 2:
            return True
    return False

def previous_leave_deductions(leave_day, user_profile):
    
    print(f"Leave Applied Date {leave_day},for user {user_profile}")

    exists = AppliedLeaves.objects.filter(
        user_profile = user_profile,
        leave_date = leave_day,
        leave_type__code__in=['CL', 'PL', 'LWP']).first()
    print("check if leave exists",exists)
    if exists:
        # next
        prev_day = exists.leave_date - timedelta(days=1)
        print("prev_day %s",prev_day)
        prev_to_prev_day = exists.leave_date - timedelta(days=2)
        print("prev_to_prev_day %s",prev_to_prev_day)

        # previous day leave in CL, PL or LWP
        prev_day_leave = AppliedLeaves.objects.filter(user_profile=user_profile, leave_date=prev_day ,leave_type__code__in=['CL', 'PL', 'LWP']).exists()

        # Previous to previous day leave in SL
        prev_to_prev_day_leave=AppliedLeaves.objects.filter(user_profile=user_profile, leave_date=prev_to_prev_day,leave_type__code__in=['SL']).exists()

        if prev_day_leave and prev_to_prev_day_leave:
            print("leave before prev and prev to prev day is true")

            # Go 5 days back to check if that was satuday and SL leave was applied for that
            days_5_before = exists.leave_date - timedelta(days=5)
            print("days_5_before", days_5_before)
            weekend_dates = [exists.leave_date - timedelta(days=4), exists.leave_date - timedelta(days=3)]
            return True , weekend_dates
        
        return False, []
    
    return False, []

    


def check_and_create_sandwich_leaves(user_profile, sandwich_day):
    """
    Create sandwich leaves for weekends or holidays **only** if proper leave chain exists
    before and after (with SL and CL/PL/LWP).
    """

    holidays = set(Holiday.objects.filter(is_active=True).values_list('date', flat=True))

    if sandwich_day.weekday() not in [5, 6] and sandwich_day not in holidays:
        return 0  # Not a weekend or holiday, skip

    created = 0
    valid_sandwich = False

    # 1. Previous SL
    previous_sl = AppliedLeaves.objects.filter(
        user_profile=user_profile,
        leave_date__lt=sandwich_day,
        leave_type__code='SL'
    ).order_by('-leave_date').first()

    # 2. Next SL
    next_sl = AppliedLeaves.objects.filter(
        user_profile=user_profile,
        leave_date__gt=sandwich_day,
        leave_type__code='SL'
    ).order_by('leave_date').first()

    if previous_sl and has_continuous_cl_pl_lwp(user_profile, previous_sl.leave_date, 'backward'):
        if has_no_working_gap(user_profile, previous_sl.leave_date, sandwich_day):
            valid_sandwich = True

    if next_sl and has_continuous_cl_pl_lwp(user_profile, next_sl.leave_date, 'forward'):
        if has_no_working_gap(user_profile, sandwich_day, next_sl.leave_date):
            valid_sandwich = True

    if valid_sandwich:
        # Find a safe range like Fri to next Mon, and check each date for holiday/weekend
        for offset in range(-3, 4):  # Wider buffer range
            day = sandwich_day + timedelta(days=offset)
            if day.weekday() in [5, 6] or day in holidays:
                exists = AppliedLeaves.objects.filter(
                    user_profile=user_profile,
                    leave_date=day
                ).exists()

                if not exists:
                    create_auto_leave_entry(user_profile, day)
                    created += 1

    return created

def handle_sandwich_leave(user_profile, applied_date):
    auto_applied = 0

   
    # Get all existing leave dates
    existing_leaves = set(
        AppliedLeaves.objects.filter(
            user_profile=user_profile,
            status__in=["Approved", "Pending", "Auto-Approved"]
        ).values_list("leave_date", flat=True)
    )

    # Get all holidays
    holidays = set(Holiday.objects.values_list("date", flat=True))

    # Get previous leave date before applied date
    previous = AppliedLeaves.objects.filter(
        user_profile=user_profile,
        leave_date__lt=applied_date,
        status__in=["Approved", "Pending", "Auto-Approved"]
    ).order_by('-leave_date').first()

    # Get next leave date after applied date
    next = AppliedLeaves.objects.filter(
        user_profile=user_profile,
        leave_date__gt=applied_date,
        status__in=["Approved", "Pending", "Auto-Approved"]
    ).order_by('leave_date').first()

    

    # --- Check for sandwich BEFORE ---
    if previous:
        prev_date = previous.leave_date
        if is_sandwich(prev_date, applied_date, existing_leaves, holidays):
            auto_applied += apply_between_dates(user_profile, prev_date, applied_date, existing_leaves, holidays)

    # --- Check for sandwich AFTER ---
    if next:
        next_date = next.leave_date
        if is_sandwich(applied_date, next_date, existing_leaves, holidays):
            auto_applied += apply_between_dates(user_profile, applied_date, next_date, existing_leaves, holidays)

    return auto_applied
def is_sandwich(start_date, end_date, existing_leaves, holidays):
    
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    current = start_date + timedelta(days=1)

    while current < end_date:
        if current in existing_leaves:
            return False
        if current.weekday() not in [5, 6] and current not in holidays:
            return False
        current += timedelta(days=1)

    return True

def apply_between_dates(user_profile, start_date, end_date, existing_leaves, holidays):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    current = start_date + timedelta(days=1)
    auto_applied = 0

    while current < end_date:
        if current not in existing_leaves and (current.weekday() in [5, 6] or current in holidays):
            if create_auto_leave_entry(user_profile, current):
                auto_applied += 1
        current += timedelta(days=1)

    return auto_applied



def combined_sandwich_handler(user_profile, leave_dates, leave_type):
    auto_deducted_days = 0
    leave_code = leave_type.code.upper()
    checked_dates = set()  # to avoid duplicate weekend/holiday checks

    for date, _ in leave_dates:
        
        if leave_code in ['CL', 'PL', 'LWP']:
            leave_date_str = date.strftime('%Y-%m-%d')
            auto_deducted_days += handle_sandwich_leave(user_profile, leave_date_str)

        
        for offset in [-2, -1, 1, 2]:
            check_date = date + timedelta(days=offset)
            if check_date not in checked_dates:
                auto_deducted_days += check_and_create_sandwich_leaves(user_profile, check_date)
                checked_dates.add(check_date)

    return auto_deducted_days


