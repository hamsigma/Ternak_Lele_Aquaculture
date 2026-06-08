from rest_framework import serializers
from .models import Penyakit, Obat, ArtikelEdukasi


class ObatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Obat
        fields = ["id", "nama_obat", "dosis", "cara_penggunaan", "catatan"]


class PenyakitSerializer(serializers.ModelSerializer):
    obat_list = ObatSerializer(many=True, read_only=True)

    class Meta:
        model = Penyakit
        fields = [
            "id", "nama", "nama_ilmiah", "deskripsi", "gejala",
            "penyebab", "penanganan", "pencegahan", "gambar_referensi",
            "obat_list", "created_at",
        ]


class ArtikelEdukasiSerializer(serializers.ModelSerializer):
    penyakit_nama = serializers.CharField(source="penyakit.nama", read_only=True)

    class Meta:
        model = ArtikelEdukasi
        fields = ["id", "judul", "konten", "kategori", "penyakit", "penyakit_nama", "created_at"]
