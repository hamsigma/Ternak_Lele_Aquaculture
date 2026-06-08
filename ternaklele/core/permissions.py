"""Shared DRF permissions untuk Ternak Lele."""
from rest_framework.permissions import BasePermission


class IsPakar(BasePermission):
    """Hanya user dengan role 'pakar' yang diizinkan."""
    message = "Akses ditolak. Hanya Pakar Perikanan yang dapat melakukan aksi ini."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_pakar


class IsPembudidaya(BasePermission):
    """Hanya user dengan role 'pembudidaya' yang diizinkan."""
    message = "Akses ditolak. Hanya Pembudidaya yang dapat melakukan aksi ini."

    def has_permission(self, request, view):
        return request.user.is_authenticated and not request.user.is_pakar


class IsPakarOrReadOnly(BasePermission):
    """Pakar bisa write, semua authenticated user bisa read."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.is_pakar
