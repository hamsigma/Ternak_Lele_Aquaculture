from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "lokasi_kolam", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Info Tambahan", {"fields": ("role", "no_telepon", "lokasi_kolam")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Info Tambahan", {"fields": ("role", "no_telepon", "lokasi_kolam")}),
    )
