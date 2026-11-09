from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPakar
from .models import DetectionLog
from .serializers import DetectionLogSerializer, DetectionUploadSerializer, ValidasiPakarSerializer
from .tasks import run_detection


class DetectionUploadView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = DetectionUploadSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user if request.user.is_authenticated else None
            log = serializer.save(user=user)
            # Jalankan deteksi secara asinkronus via Celery / eager
            run_detection.delay(log.id)
            return Response(
                {"id": log.id, "status": "Gambar diterima, sedang diproses..."},
                status=status.HTTP_202_ACCEPTED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DetectionResultView(generics.RetrieveAPIView):
    serializer_class = DetectionLogSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DetectionLog.objects.all()


class DetectionHistoryView(generics.ListAPIView):
    serializer_class = DetectionLogSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return DetectionLog.objects.filter(user=self.request.user)
        return DetectionLog.objects.all()[:20]


class ValidasiPakarView(generics.UpdateAPIView):
    serializer_class = ValidasiPakarSerializer
    permission_classes = [IsPakar]
    queryset = DetectionLog.objects.all()
    http_method_names = ["patch"]


class SemuaDeteksiView(generics.ListAPIView):
    """Hanya untuk Pakar: melihat semua log deteksi."""
    serializer_class = DetectionLogSerializer
    permission_classes = [IsPakar]
    queryset = DetectionLog.objects.select_related("user").all()
