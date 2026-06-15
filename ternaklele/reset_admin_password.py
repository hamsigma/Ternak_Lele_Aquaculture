import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    admin_user = User.objects.get(username="admin")
    admin_user.set_password("admin123")
    admin_user.save()
    print("[OK] Password untuk user 'admin' berhasil disetel menjadi 'admin123'")
except User.DoesNotExist:
    # Jika tidak ada, buat baru
    User.objects.create_superuser("admin", "admin@ternaklele.id", "admin123")
    print("[OK] User superuser 'admin' baru berhasil dibuat dengan password 'admin123'")
