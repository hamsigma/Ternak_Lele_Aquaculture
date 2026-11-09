import os
import io
import sys
import hashlib
from pathlib import Path
from PIL import Image
import pandas as pd
from huggingface_hub import hf_hub_download

BASE_DIR = Path(r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele\dataset\fish_disease")
TARGET_CLASSES = ["Aeromonas", "Jamur", "Parasit", "Overfeeding", "Sehat"]

# Unduh train dan test parquet dari panda992/fish_disease_datasets
print("[1/4] Mengunduh & memuat parquet Hugging Face...")
train_parquet = hf_hub_download(
    repo_id="panda992/fish_disease_datasets",
    filename="data/train-00000-of-00001.parquet",
    repo_type="dataset"
)
test_parquet = hf_hub_download(
    repo_id="panda992/fish_disease_datasets",
    filename="data/test-00000-of-00001.parquet",
    repo_type="dataset"
)

# Mapping HF label ke kelas target kita
# '0': Bacterial Red disease -> Aeromonas
# '1': Bacterial diseases - Aeromoniasis -> Aeromonas
# '3': Fungal diseases Saprolegniasis -> Jamur
# '4': Healthy Fish -> Sehat
# '5': Parasitic diseases -> Parasit
LABEL_MAPPING = {
    0: "Aeromonas",
    1: "Aeromonas",
    3: "Jamur",
    4: "Sehat",
    5: "Parasit"
}

print("[2/4] Mengekstrak gambar patogen & kontrol dari Hugging Face...")
extracted_counts = {c: 0 for c in TARGET_CLASSES}

for p_file in [train_parquet, test_parquet]:
    df = pd.read_parquet(p_file)
    for idx, row in df.iterrows():
        lbl = row["label"]
        if lbl in LABEL_MAPPING:
            target_class = LABEL_MAPPING[lbl]
            folder = BASE_DIR / target_class
            folder.mkdir(parents=True, exist_ok=True)
            try:
                raw_bytes = row["image"]["bytes"]
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                if img.width >= 50 and img.height >= 50:
                    extracted_counts[target_class] += 1
                    out_path = folder / f"hf_{target_class.lower()}_{extracted_counts[target_class]:04d}.jpg"
                    img.save(out_path, format="JPEG", quality=95)
            except Exception:
                continue

for c, count in extracted_counts.items():
    if count > 0:
        print(f"  • {c:<12}: {count} gambar diekstrak dari Hugging Face")

print("\n[3/4] Melakukan pembersihan data, verifikasi & deduplikasi...")
seen_hashes = set()
total_cleaned = 0

for cls in TARGET_CLASSES:
    folder = BASE_DIR / cls
    all_files = sorted(list(folder.glob("*.*")))
    kept_images = []
    
    for f in all_files:
        if f.name == ".gitkeep":
            continue
        try:
            with Image.open(f) as img:
                img.verify()
            with Image.open(f) as img:
                img = img.convert("RGB")
                w, h = img.size
                if w < 50 or h < 50:
                    f.unlink()
                    continue
                # Hash untuk deduplikasi gambar identik
                file_hash = hashlib.md5(img.tobytes()).hexdigest()
                if file_hash in seen_hashes:
                    f.unlink()
                    continue
                seen_hashes.add(file_hash)
                kept_images.append((f, img))
        except Exception:
            try:
                f.unlink()
            except Exception:
                pass

    # Bersihkan file non-kept di folder
    for f in list(folder.glob("*.jpg")) + list(folder.glob("*.png")):
        try:
            f.unlink()
        except Exception:
            pass

    # Simpan kembali dengan nama seragam: [kelas]_[nomor].jpg
    for i, (f, img) in enumerate(kept_images, start=1):
        clean_name = folder / f"{cls.lower()}_{i:04d}.jpg"
        img.save(clean_name, format="JPEG", quality=95)
    
    final_count = len(list(folder.glob("*.jpg")))
    total_cleaned += final_count
    print(f"  • {cls:<15}: {final_count} gambar bersih siap latih")

print(f"\n[4/4] Dataset Final: Total {total_cleaned} gambar bersih di 5 kelas target!")
