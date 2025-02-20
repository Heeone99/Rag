from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('qna/', include('qna.urls')),
    path('lecture/', include('lecture.urls')),
    path('storage/', include('storage.urls')),
]
