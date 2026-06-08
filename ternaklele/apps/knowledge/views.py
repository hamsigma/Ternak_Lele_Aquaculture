from rest_framework import generics, permissions, filters
from .models import Penyakit, ArtikelEdukasi
from .serializers import PenyakitSerializer, ArtikelEdukasiSerializer


class PenyakitListView(generics.ListAPIView):
    queryset = Penyakit.objects.prefetch_related("obat_list").all()
    serializer_class = PenyakitSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nama", "gejala"]


class PenyakitDetailView(generics.RetrieveAPIView):
    queryset = Penyakit.objects.prefetch_related("obat_list").all()
    serializer_class = PenyakitSerializer
    permission_classes = [permissions.AllowAny]


class ArtikelListView(generics.ListAPIView):
    queryset = ArtikelEdukasi.objects.select_related("penyakit").all()
    serializer_class = ArtikelEdukasiSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ["judul", "kategori"]


class ArtikelDetailView(generics.RetrieveAPIView):
    queryset = ArtikelEdukasi.objects.select_related("penyakit").all()
    serializer_class = ArtikelEdukasiSerializer
    permission_classes = [permissions.AllowAny]

