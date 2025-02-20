from django.urls import path
from . import views

urlpatterns = [
    path('', views.qna, name='qna'),  # '/qna/'를 처리하는 뷰
    path('get_chat_history/', views.get_chat_history, name='get_chat_history'),
    path('save_chat/', views.save_chat, name='save_chat'),
]
