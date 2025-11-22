from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from ..models import Role





def role_management_page(request):
    return render(request, 'roles.html')

