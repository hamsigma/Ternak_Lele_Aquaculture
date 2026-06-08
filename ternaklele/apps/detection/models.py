from django.db import models
from django.conf import settings


class DetectionLog(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Menunggu"
        PROCESSING = "processing", "Diproses"
        DONE = "done", "Selesai"
        FAILED = "failed", "Gagal"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="detection_logs"
    )
    image = models.ImageField(upload_to="deteksi/%Y/%m/")
    penyakit_terdeteksi = models.CharField(max_length=100, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    semua_probabilitas = models.JSONField(default=dict, blank=True)
    rekomendasi_penanganan = models.TextField(blank=True)
    status_validasi = models.BooleanField(
        null=True,
        blank=True,
        help_text="True=Valid, False=Invalid, None=Belum divalidasi"
    )
    status_proses = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    catatan_pakar = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log Deteksi"
        verbose_name_plural = "Log Deteksi"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Deteksi #{self.id} - {self.user.username} - {self.penyakit_terdeteksi or 'Pending'}"
