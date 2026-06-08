import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DetectionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="deteksi/%Y/%m/")),
                ("penyakit_terdeteksi", models.CharField(blank=True, max_length=100)),
                ("confidence_score", models.FloatField(blank=True, null=True)),
                ("semua_probabilitas", models.JSONField(blank=True, default=dict)),
                ("rekomendasi_penanganan", models.TextField(blank=True)),
                ("status_validasi", models.BooleanField(
                    blank=True,
                    help_text="True=Valid, False=Invalid, None=Belum divalidasi",
                    null=True,
                )),
                ("status_proses", models.CharField(
                    choices=[
                        ("pending", "Menunggu"),
                        ("processing", "Diproses"),
                        ("done", "Selesai"),
                        ("failed", "Gagal"),
                    ],
                    default="pending",
                    max_length=20,
                )),
                ("catatan_pakar", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="detection_logs",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"verbose_name": "Log Deteksi", "verbose_name_plural": "Log Deteksi", "ordering": ["-created_at"]},
        ),
    ]
