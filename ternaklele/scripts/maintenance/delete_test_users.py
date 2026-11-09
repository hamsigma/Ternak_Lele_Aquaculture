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
from apps.chatbot.models import ChatSession, ChatMessage
from apps.detection.models import DetectionLog

User = get_user_model()

print("=== DAFTAR USER SEBELUM DIHAPUS ===")
users = User.objects.all()
for u in users:
    print(f"- Username: {u.username} | Email: {u.email} | Superuser: {u.is_superuser}")

# Hapus semua user yang bukan superuser (user test)
test_users = User.objects.filter(is_superuser=False)
count = test_users.count()

print(f"\nMenghapus {count} user test...")
for tu in test_users:
    # Hapus data terkait terlebih dahulu jika diperlukan
    ChatSession.objects.filter(user=tu).delete()
    DetectionLog.objects.filter(user=tu).delete()
    print(f"Menghapus user: {tu.username}")
    tu.delete()

print("\n=== DAFTAR USER SEKARANG ===")
for u in User.objects.all():
    print(f"- Username: {u.username} | Email: {u.email} | Superuser: {u.is_superuser}")

print("\nSelesai!")
