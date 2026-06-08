"""
Model untuk menyimpan embedding dokumen knowledge di pgvector.
Digunakan untuk semantic search pada RAG pipeline.
"""
from django.db import models


class KnowledgeVector(models.Model):
    """
    Menyimpan embedding dari konten knowledge base (penyakit/artikel).
    Field embedding menggunakan pgvector VectorField.
    """
    SOURCE_CHOICES = [
        ("penyakit", "Penyakit"),
        ("artikel", "Artikel Edukasi"),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_id = models.PositiveIntegerField()
    content = models.TextField(help_text="Teks asli yang di-embed")
    # VectorField membutuhkan pgvector extension di PostgreSQL
    # Diinisialisasi dinamis untuk menghindari import error jika pgvector belum diinstall
    embedding = models.JSONField(
        help_text="Vector embedding disimpan sebagai JSON fallback. "
                  "Ganti dengan pgvector.django.VectorField di production.",
        default=list,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "chatbot"
        verbose_name = "Knowledge Vector"
        verbose_name_plural = "Knowledge Vectors"
        indexes = [
            models.Index(fields=["source_type", "source_id"]),
        ]

    def __str__(self):
        return f"{self.source_type}:{self.source_id} - {self.content[:60]}"
