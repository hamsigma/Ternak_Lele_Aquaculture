import os
import sys
import django

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

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
