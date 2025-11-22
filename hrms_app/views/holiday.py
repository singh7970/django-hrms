
from ..models.holiday import Holiday
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..models.holiday import Holiday
import json
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.dateparse import parse_date


@method_decorator(csrf_exempt, name='dispatch')
class HolidayAPIView(View):
    def get(self, request):
        holidays = Holiday.objects.filter(is_active=True).order_by('date')
        data = [{
            'id': holiday.id,
            'date': holiday.date.strftime('%Y-%m-%d'),
            'occasion': holiday.occasion
        } for holiday in holidays]
        return JsonResponse(data, safe=False)

    def post(self, request):
        try:
            data = json.loads(request.body)
            date = parse_date(data.get('date'))
            occasion = data.get('occasion', '').strip()

            if not date or not occasion:
                return JsonResponse({'error': 'Date and occasion are required.'}, status=400)

            # Optional: check for duplicate date
            if Holiday.objects.filter(date=date, is_active=True).exists():
                return JsonResponse({'error': 'Holiday already exists for this date.'}, status=409)

            holiday = Holiday.objects.create(
                date=date,
                occasion=occasion,
                row_created_by=request.user.username if request.user.is_authenticated else 'sysusr'
            )
            return JsonResponse({
                'id': holiday.id,
                'date': holiday.date.strftime('%Y-%m-%d'),
                'occasion': holiday.occasion
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class HolidayDetailAPIView(View):
    def put(self, request, pk):
        try:
            data = json.loads(request.body)
            date = parse_date(data.get('date'))
            occasion = data.get('occasion', '').strip()

            if not date or not occasion:
                return JsonResponse({'error': 'Date and occasion are required.'}, status=400)

            holiday = Holiday.objects.get(pk=pk, is_active=True)
            holiday.date = date
            holiday.occasion = occasion
            holiday.row_modified_by = request.user.username if request.user.is_authenticated else 'sysusr'
            holiday.save()

            return JsonResponse({
                'id': holiday.id,
                'date': holiday.date.strftime('%Y-%m-%d'),
                'occasion': holiday.occasion
            }, status=200)

        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Holiday not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def delete(self, request, pk):
        try:
            holiday = Holiday.objects.get(pk=pk, is_active=True)
            holiday.is_active = False
            holiday.save()
            return JsonResponse({'status': 'deleted'}, status=200)

        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Holiday not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
def holiday_page(request):
    return render(request, 'holiday.html')