from django.urls import path
from .views import LectureSummaryView, LectureQAView

urlpatterns = [
    path("summary/", LectureSummaryView.as_view(), name="lecture-summary"),
    path("qa/", LectureQAView.as_view(), name="lecture-qa"),
]
