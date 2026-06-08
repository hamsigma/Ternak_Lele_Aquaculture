from django.db import models


class Penyakit(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    nama_ilmiah = models.CharField(max_length=150, blank=True)
    deskripsi = models.TextField()
    gejala = models.TextField()
    penyebab = models.TextField()
    penanganan = models.TextField()
    pencegahan = models.TextField(blank=True)
    gambar_referensi = models.ImageField(upload_to="penyakit/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Penyakit"
        verbose_name_plural = "Penyakit"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class Obat(models.Model):
    penyakit = models.ForeignKey(Penyakit, on_delete=models.CASCADE, related_name="obat_list")
    nama_obat = models.CharField(max_length=150)
    dosis = models.CharField(max_length=200)
    cara_penggunaan = models.TextField()
    catatan = models.TextField(blank=True)

    class Meta:
        verbose_name = "Obat"
        verbose_name_plural = "Obat"

    def __str__(self):
        return f"{self.nama_obat} - {self.penyakit.nama}"


class ArtikelEdukasi(models.Model):
    judul = models.CharField(max_length=255)
    konten = models.TextField()
    kategori = models.CharField(max_length=100, blank=True)
    penyakit = models.ForeignKey(Penyakit, on_delete=models.SET_NULL, null=True, blank=True, related_name="artikel")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Artikel Edukasi"
        verbose_name_plural = "Artikel Edukasi"
        ordering = ["-created_at"]

    def __str__(self):
        return self.judul
