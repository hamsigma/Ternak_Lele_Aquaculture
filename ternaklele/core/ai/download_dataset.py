"""
Script download & persiapan dataset dari Kaggle.

Dataset: Freshwater Fish Disease Aquaculture In South Asia
URL    : https://www.kaggle.com/datasets/subirbiswas19/freshwater-fish-disease-aquaculture-in-south-asia
Kelas  : 7 kelas × 250 gambar = 1750 gambar total

Prasyarat:
  pip install kaggle
  Letakkan kaggle.json di ~/.kaggle/kaggle.json
  (Download dari https://www.kaggle.com/settings → API → Create New Token)

Cara jalankan:
  python core/ai/download_dataset.py --output ./dataset
"""

import argparse
import os
import zipfile
from pathlib import Path


KAGGLE_DATASET = "subirbiswas19/freshwater-fish-disease-aquaculture-in-south-asia"
DATASET_DIR_NAME = "fish_disease"


def check_kaggle_credentials():
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json.exists():
        print("ERROR: File kaggle.json tidak ditemukan!")
        print("Langkah setup:")
        print("  1. Buka https://www.kaggle.com/settings")
        print("  2. Scroll ke bagian 'API' → klik 'Create New Token'")
        print("  3. File kaggle.json akan terdownload otomatis")
        print(f"  4. Pindahkan ke: {kaggle_json}")
        print("  5. Jalankan script ini lagi")
        return False
    return True


def download_dataset(output_dir: str):
    if not check_kaggle_credentials():
        return False

    try:
        import kaggle
    except ImportError:
        print("ERROR: Package 'kaggle' belum terinstall.")
        print("Jalankan: pip install kaggle")
        return False

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    dataset_path = output_path / DATASET_DIR_NAME
    if dataset_path.exists() and any(dataset_path.iterdir()):
        print(f"Dataset sudah ada di: {dataset_path}")
        print("Gunakan --force untuk download ulang.")
        return True

    print(f"Downloading dataset: {KAGGLE_DATASET}")
    print(f"Tujuan: {output_path}\n")

    # Download via Kaggle API
    kaggle.api.dataset_download_files(
        KAGGLE_DATASET,
        path=str(output_path),
        unzip=True,
    )

    # Cari dan normalisasi struktur folder hasil download
    _normalize_folder_structure(output_path, dataset_path)

    print(f"\nDataset siap di: {dataset_path}")
    _print_dataset_summary(dataset_path)
    return True


def _normalize_folder_structure(base_path: Path, target_path: Path):
    """
    Normalize struktur folder — pastikan target_path berisi subfolder per kelas.
    Kaggle kadang mengekstrak dengan nested folder tambahan.
    """
    # Cari folder yang berisi subfolder gambar
    for item in base_path.iterdir():
        if item.is_dir() and item.name != DATASET_DIR_NAME:
            subdirs = [d for d in item.iterdir() if d.is_dir()]
            if subdirs:
                # Pindahkan ke target_path
                import shutil
                if not target_path.exists():
                    shutil.move(str(item), str(target_path))
                    print(f"Folder dipindahkan: {item.name} → {target_path.name}")
                return

    # Jika tidak ada nested, buat target_path dari base
    if not target_path.exists():
        target_path.mkdir()


def _print_dataset_summary(dataset_path: Path):
    print("\n=== Summary Dataset ===")
    total = 0
    for folder in sorted(dataset_path.iterdir()):
        if folder.is_dir():
            count = len(list(folder.glob("*.jpg"))) + \
                    len(list(folder.glob("*.jpeg"))) + \
                    len(list(folder.glob("*.png")))
            print(f"  {folder.name:40s} : {count:4d} gambar")
            total += count
    print(f"  {'TOTAL':40s} : {total:4d} gambar")


def augment_dataset(dataset_path: str, target_per_class: int = 500):
    """
    Augmentasi gambar untuk kelas yang kurang dari target_per_class.
    Menggunakan Albumentations untuk augmentasi yang lebih kaya.
    """
    try:
        import albumentations as A
        from PIL import Image
        import numpy as np
        import random
    except ImportError:
        print("Albumentations tidak tersedia, skip augmentasi.")
        print("Install dengan: pip install albumentations")
        return

    aug = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.RandomRotate90(p=0.3),
        A.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, p=0.7),
        A.GaussNoise(p=0.2),
        A.Blur(blur_limit=3, p=0.1),
        A.ElasticTransform(p=0.1),
        A.RandomBrightnessContrast(p=0.3),
    ])

    dataset_path = Path(dataset_path)
    print("\n=== Augmentasi Dataset ===")

    for folder in dataset_path.iterdir():
        if not folder.is_dir():
            continue

        images = list(folder.glob("*.jpg")) + list(folder.glob("*.jpeg")) + list(folder.glob("*.png"))
        current_count = len(images)

        if current_count >= target_per_class:
            print(f"  {folder.name}: {current_count} gambar (sudah cukup, skip)")
            continue

        needed = target_per_class - current_count
        print(f"  {folder.name}: {current_count} → {target_per_class} ({needed} augmentasi)")

        aug_dir = folder / "augmented"
        aug_dir.mkdir(exist_ok=True)

        for i in range(needed):
            src_img = random.choice(images)
            img = np.array(Image.open(src_img).convert("RGB"))
            result = aug(image=img)["image"]
            out_path = aug_dir / f"aug_{i:04d}.jpg"
            Image.fromarray(result).save(out_path, quality=90)

    print("Augmentasi selesai!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download & persiapan dataset Ternak Lele")
    parser.add_argument("--output", type=str, default="./dataset",
                        help="Folder tujuan dataset")
    parser.add_argument("--augment", action="store_true",
                        help="Augmentasi kelas yang kurang gambar")
    parser.add_argument("--target_per_class", type=int, default=500,
                        help="Target jumlah gambar per kelas setelah augmentasi")
    parser.add_argument("--force", action="store_true",
                        help="Download ulang meski dataset sudah ada")

    args = parser.parse_args()

    if args.force:
        import shutil
        target = Path(args.output) / DATASET_DIR_NAME
        if target.exists():
            shutil.rmtree(target)
            print("Dataset lama dihapus.")

    success = download_dataset(args.output)

    if success and args.augment:
        augment_dataset(
            str(Path(args.output) / DATASET_DIR_NAME),
            args.target_per_class
        )
