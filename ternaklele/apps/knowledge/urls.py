from django.urls import path
from .views import PenyakitListView, PenyakitDetailView, ArtikelListView, ArtikelDetailView

urlpatterns = [
    path("penyakit/", PenyakitListView.as_view(), name="penyakit-list"),
    path("penyakit/<int:pk>/", PenyakitDetailView.as_view(), name="penyakit-detail"),
    path("artikel/", ArtikelListView.as_view(), name="artikel-list"),
    path("artikel/<int:pk>/", ArtikelDetailView.as_view(), name="artikel-detail"),
]
