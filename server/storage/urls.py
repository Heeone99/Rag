from django.urls import path
from storage.views import read_csv, webhook

urlpatterns = [
    path('read-csv/', read_csv, name='read_csv'),
    path('webhook/', webhook, name='webhook'),  # Webhook 엔드포인트 추가
]
