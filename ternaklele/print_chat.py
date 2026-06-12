import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
from apps.chatbot.models import ChatMessage
for msg in ChatMessage.objects.order_by('-id')[:10]:
    print(f"--- {msg.sender_type.upper()} ({msg.created_at}) ---")
    print(msg.message_text)
