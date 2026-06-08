from django.urls import path
from .views import (
    DetectionUploadView,
    DetectionResultView,
    DetectionHistoryView,
    ValidasiPakarView,
    SemuaDeteksiView,
)

urlpatterns = [
    path("upload/", DetectionUploadView.as_view(), name="detection-upload"),
    path("result/<int:pk>/", DetectionResultView.as_view(), name="detection-result"),
    path("history/", DetectionHistoryView.as_view(), name="detection-history"),
    path("validasi/<int:pk>/", ValidasiPakarView.as_view(), name="detection-validasi"),
    path("semua/", SemuaDeteksiView.as_view(), name="detection-semua"),
]
