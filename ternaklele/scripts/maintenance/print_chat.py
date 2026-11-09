import os, sys, django

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
from apps.chatbot.models import ChatMessage
for msg in ChatMessage.objects.order_by('-id')[:10]:
    print(f"--- {msg.sender_type.upper()} ({msg.created_at}) ---")
    print(msg.message_text)
