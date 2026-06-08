from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatbot", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="KnowledgeVector",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(
                    choices=[("penyakit", "Penyakit"), ("artikel", "Artikel Edukasi")],
                    max_length=20,
                )),
                ("source_id", models.PositiveIntegerField()),
                ("content", models.TextField(help_text="Teks asli yang di-embed")),
                ("embedding", models.JSONField(default=list, help_text="Vector embedding")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Knowledge Vector",
                "verbose_name_plural": "Knowledge Vectors",
            },
        ),
        migrations.AddIndex(
            model_name="knowledgevector",
            index=models.Index(fields=["source_type", "source_id"], name="chatbot_kno_source__idx"),
        ),
    ]
