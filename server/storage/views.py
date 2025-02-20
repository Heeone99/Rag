import csv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import os
import json

@csrf_exempt
def read_csv(request):
    if request.method == 'GET':
        csv_path = os.path.join(settings.BASE_DIR, 'data/csv/mjc_promotion.csv')
        
        if not os.path.exists(csv_path):
            return JsonResponse({'error': 'CSV file not found'}, status=404)

        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                csv_data = [row for row in reader]

            # 데이터를 JSON으로 변환
            return JsonResponse({'data': csv_data, 'message': 'CSV file read successfully'}, json_dumps_params={'ensure_ascii': False})
        except UnicodeDecodeError:
            return JsonResponse({'error': 'Failed to decode file. Check file encoding.'}, status=500)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        try:
            # 요청 데이터 처리
            data = json.loads(request.body)
            topic = data.get('topic')

            if not topic:
                return JsonResponse({'error': 'Topic is required'}, status=400)

            # n8n 웹훅 보내기
            n8n_url = "http://localhost:5678/webhook-test/f83991cb-a2eb-4875-95ef-fc475bae9ed1"
            response = requests.post(n8n_url, json={"topic": topic})

            if response.status_code == 200:
                return JsonResponse(response.json(), status=200)
            else:
                return JsonResponse({'error': 'n8n request failed', 'details': response.text}, status=response.status_code)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)
