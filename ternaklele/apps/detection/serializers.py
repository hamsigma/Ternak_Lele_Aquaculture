from rest_framework import serializers
from PIL import Image as PilImage

from .models import DetectionLog

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_FILE_SIZE_MB = 10


class DetectionLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    confidence_persen = serializers.SerializerMethodField()

    class Meta:
        model = DetectionLog
        fields = [
            "id", "user_username", "image", "penyakit_terdeteksi",
            "confidence_score", "confidence_persen", "semua_probabilitas",
            "rekomendasi_penanganan", "status_validasi", "status_proses",
            "catatan_pakar", "created_at",
        ]
        read_only_fields = [
            "penyakit_terdeteksi", "confidence_score", "semua_probabilitas",
            "rekomendasi_penanganan", "status_proses", "created_at", "user_username",
            "confidence_persen",
        ]

    def get_confidence_persen(self, obj) -> str:
        if obj.confidence_score is not None:
            return f"{obj.confidence_score * 100:.1f}%"
        return "-"


class DetectionUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionLog
        fields = ["image"]

    def validate_image(self, value):
        # Validasi ukuran file
        if value.size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise serializers.ValidationError(
                f"Ukuran gambar maksimal {MAX_FILE_SIZE_MB}MB."
            )

        # Validasi format menggunakan Pillow
        try:
            img = PilImage.open(value)
            img.verify()
        except Exception:
            raise serializers.ValidationError("File bukan gambar yang valid.")

        # Reset pointer setelah verify
        value.seek(0)
        img = PilImage.open(value)
        if img.format not in ALLOWED_FORMATS:
            raise serializers.ValidationError(
                f"Format gambar tidak didukung. Gunakan: {', '.join(ALLOWED_FORMATS)}."
            )

        value.seek(0)
        return value


class ValidasiPakarSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionLog
        fields = ["status_validasi", "catatan_pakar"]
