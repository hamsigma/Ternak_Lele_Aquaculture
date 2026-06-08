import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("context_summary", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="chat_sessions",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"verbose_name": "Sesi Chat", "verbose_name_plural": "Sesi Chat", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender_type", models.CharField(
                    choices=[("user", "Pengguna"), ("ai", "AI")],
                    max_length=10,
                )),
                ("message_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="messages",
                    to="chatbot.chatsession",
                )),
            ],
            options={"verbose_name": "Pesan Chat", "verbose_name_plural": "Pesan Chat", "ordering": ["created_at"]},
        ),
    ]
