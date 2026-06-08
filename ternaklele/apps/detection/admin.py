from django.contrib import admin
from .models import DetectionLog


@admin.register(DetectionLog)
class DetectionLogAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "penyakit_terdeteksi", "confidence_score", "status_proses", "status_validasi", "created_at"]
    list_filter = ["status_proses", "status_validasi", "penyakit_terdeteksi"]
    search_fields = ["user__username", "penyakit_terdeteksi"]
    readonly_fields = ["semua_probabilitas", "created_at"]
    list_editable = ["status_validasi"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")
