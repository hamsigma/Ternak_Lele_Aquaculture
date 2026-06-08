import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Penyakit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nama", models.CharField(max_length=100, unique=True)),
                ("nama_ilmiah", models.CharField(blank=True, max_length=150)),
                ("deskripsi", models.TextField()),
                ("gejala", models.TextField()),
                ("penyebab", models.TextField()),
                ("penanganan", models.TextField()),
                ("pencegahan", models.TextField(blank=True)),
                ("gambar_referensi", models.ImageField(blank=True, null=True, upload_to="penyakit/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Penyakit", "verbose_name_plural": "Penyakit", "ordering": ["nama"]},
        ),
        migrations.CreateModel(
            name="Obat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nama_obat", models.CharField(max_length=150)),
                ("dosis", models.CharField(max_length=200)),
                ("cara_penggunaan", models.TextField()),
                ("catatan", models.TextField(blank=True)),
                ("penyakit", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="obat_list",
                    to="knowledge.penyakit",
                )),
            ],
            options={"verbose_name": "Obat", "verbose_name_plural": "Obat"},
        ),
        migrations.CreateModel(
            name="ArtikelEdukasi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("judul", models.CharField(max_length=255)),
                ("konten", models.TextField()),
                ("kategori", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("penyakit", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="artikel",
                    to="knowledge.penyakit",
                )),
            ],
            options={"verbose_name": "Artikel Edukasi", "verbose_name_plural": "Artikel Edukasi", "ordering": ["-created_at"]},
        ),
    ]
