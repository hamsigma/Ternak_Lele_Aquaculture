from django.contrib import admin
from .models import Penyakit, Obat, ArtikelEdukasi


class ObatInline(admin.TabularInline):
    model = Obat
    extra = 1


@admin.register(Penyakit)
class PenyakitAdmin(admin.ModelAdmin):
    list_display = ["nama", "nama_ilmiah", "updated_at"]
    search_fields = ["nama", "gejala"]
    inlines = [ObatInline]


@admin.register(ArtikelEdukasi)
class ArtikelAdmin(admin.ModelAdmin):
    list_display = ["judul", "kategori", "penyakit", "created_at"]
    list_filter = ["kategori", "penyakit"]
    search_fields = ["judul", "konten"]
