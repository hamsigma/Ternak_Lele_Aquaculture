"""
Management command: python manage.py download_dataset
Download dataset penyakit ikan dari Kaggle.

Prasyarat:
  pip install kaggle
  ~/.kaggle/kaggle.json harus ada (download dari kaggle.com/settings → API)
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Download dataset penyakit ikan dari Kaggle untuk training model."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output", type=str,
            default="./dataset",
            help="Folder tujuan dataset (default: ./dataset)"
        )
        parser.add_argument(
            "--augment", action="store_true",
            help="Augmentasi kelas yang kurang dari target"
        )
        parser.add_argument(
            "--target_per_class", type=int, default=500,
            help="Target gambar per kelas setelah augmentasi (default: 500)"
        )
        parser.add_argument(
            "--force", action="store_true",
            help="Hapus dan download ulang meski sudah ada"
        )

    def handle(self, *args, **options):
        import sys
        project_root = str(settings.BASE_DIR)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from core.ai.download_dataset import download_dataset, augment_dataset, DATASET_DIR_NAME
        from pathlib import Path

        if options["force"]:
            import shutil
            target = Path(options["output"]) / DATASET_DIR_NAME
            if target.exists():
                shutil.rmtree(target)
                self.stdout.write("Dataset lama dihapus.")

        self.stdout.write(f"Downloading ke: {options['output']}")
        success = download_dataset(options["output"])

        if success and options["augment"]:
            self.stdout.write("\nMemulai augmentasi...")
            augment_dataset(
                str(Path(options["output"]) / DATASET_DIR_NAME),
                options["target_per_class"],
            )

        if success:
            self.stdout.write(self.style.SUCCESS("\nDataset siap! Lanjutkan dengan:"))
            self.stdout.write(f"  python manage.py train_model --data_dir {options['output']}/fish_disease")
