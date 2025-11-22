from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

from hrms_app.models.users import UserProfile

User = get_user_model()  # Correct way to reference your custom User model



def show_login_page(request):
    if request.method == "POST": 
        email = request.POST.get("email")
        password = request.POST.get("password")

  
        try:
            user_obj = UserProfile.objects.get(email=email)
          
        except UserProfile.DoesNotExist:
            print("No user found with that email.")

        user = authenticate(username=email, password=password)
        
        if user:  
            login(request, user)
            
            
            next_url = request.GET.get("next") or "dashboard"  # Ensure it redirects properly
            return redirect(next_url)
             
        
        else: 
            messages.error(request, "Invalid email or password!") 
            return redirect("login")  

    return render(request, "login.html") 

        
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")



