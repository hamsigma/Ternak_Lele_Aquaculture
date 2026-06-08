"""
Management command: python manage.py train_model
Melatih EfficientNet-B3 untuk klasifikasi penyakit lele.

Contoh:
  python manage.py train_model --data_dir ./dataset/fish_disease
  python manage.py train_model --data_dir ./dataset/fish_disease --epochs 50 --evaluate
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Latih model EfficientNet-B3 untuk deteksi penyakit lele."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data_dir", type=str, required=True,
            help="Path ke folder dataset (subfolder per kelas)"
        )
        parser.add_argument(
            "--output", type=str,
            default=None,
            help="Path output .pth (default: settings.AI_MODEL_PATH)"
        )
        parser.add_argument("--epochs", type=int, default=30)
        parser.add_argument("--batch_size", type=int, default=32)
        parser.add_argument("--lr", type=float, default=1e-4)
        parser.add_argument(
            "--evaluate", action="store_true",
            help="Jalankan evaluasi setelah training selesai"
        )

    def handle(self, *args, **options):
        import sys
        import os

        # Tambahkan root ke sys.path agar import core.ai berjalan
        project_root = str(settings.BASE_DIR)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from core.ai.train import train_model, evaluate_model

        output_path = options["output"] or str(settings.AI_MODEL_PATH)

        self.stdout.write(f"Dataset   : {options['data_dir']}")
        self.stdout.write(f"Output    : {output_path}")
        self.stdout.write(f"Epochs    : {options['epochs']}")
        self.stdout.write(f"Batch Size: {options['batch_size']}")
        self.stdout.write(f"LR        : {options['lr']}\n")

        best_acc = train_model(
            data_dir=options["data_dir"],
            output_path=output_path,
            epochs=options["epochs"],
            batch_size=options["batch_size"],
            lr=options["lr"],
        )

        if options["evaluate"]:
            self.stdout.write("\nMenjalankan evaluasi...")
            evaluate_model(output_path, options["data_dir"], options["batch_size"])

        if best_acc >= 88.0:
            self.stdout.write(self.style.SUCCESS(
                f"\nTarget precision ≥ 88% tercapai! Best Val Acc: {best_acc:.1f}%"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"\nBest Val Acc: {best_acc:.1f}% (target ≥ 88%, coba tambah epochs atau data)"
            ))

        # Reset singleton classifier agar load model baru
        import core.ai.classifier as clf_module
        clf_module._classifier_instance = None
        self.stdout.write("Classifier singleton direset — model baru akan dimuat saat deteksi berikutnya.")
