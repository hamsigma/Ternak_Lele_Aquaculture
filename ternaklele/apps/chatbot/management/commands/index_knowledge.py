"""
Management command: python manage.py index_knowledge
Membuat embedding dari semua data Penyakit dan ArtikelEdukasi ke KnowledgeVector.
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Index seluruh knowledge base ke vector embeddings untuk RAG chatbot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Hapus semua vector lama sebelum re-index.",
        )

    def handle(self, *args, **options):
        from apps.knowledge.models import Penyakit, ArtikelEdukasi
        from apps.chatbot.vector_models import KnowledgeVector

        if not settings.OPENAI_API_KEY:
            self.stderr.write("OPENAI_API_KEY tidak dikonfigurasi. Batalkan.")
            return

        try:
            from langchain_openai import OpenAIEmbeddings
            embedder = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )
        except ImportError:
            self.stderr.write("LangChain tidak terinstall.")
            return

        if options["reset"]:
            KnowledgeVector.objects.all().delete()
            self.stdout.write("Vector lama dihapus.")

        # Index Penyakit
        penyakit_list = Penyakit.objects.prefetch_related("obat_list").all()
        self.stdout.write(f"Mengindex {penyakit_list.count()} penyakit...")

        for p in penyakit_list:
            content = (
                f"Penyakit: {p.nama}\n"
                f"Gejala: {p.gejala}\n"
                f"Penyebab: {p.penyebab}\n"
                f"Penanganan: {p.penanganan}\n"
                f"Pencegahan: {p.pencegahan}"
            )
            embedding = embedder.embed_query(content)
            KnowledgeVector.objects.update_or_create(
                source_type="penyakit",
                source_id=p.id,
                defaults={"content": content, "embedding": embedding},
            )
            self.stdout.write(f"  ✓ {p.nama}")

        # Index Artikel
        artikel_list = ArtikelEdukasi.objects.all()
        self.stdout.write(f"Mengindex {artikel_list.count()} artikel...")

        for a in artikel_list:
            content = f"Artikel: {a.judul}\n{a.konten}"
            embedding = embedder.embed_query(content[:2000])
            KnowledgeVector.objects.update_or_create(
                source_type="artikel",
                source_id=a.id,
                defaults={"content": content[:2000], "embedding": embedding},
            )
            self.stdout.write(f"  ✓ {a.judul}")

        self.stdout.write(self.style.SUCCESS("Indexing selesai!"))
