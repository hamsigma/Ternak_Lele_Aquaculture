"""
pipeline_akuisisi_resmi.py
================================================================================
Implementasi resmi pipeline akuisisi dataset sesuai spesifikasi pada:
docs/dataset_dokumentasi_pipeline_akuisisi.md

Sumber:
1. Kaggle (rukesh17/cleaned-fish-disease-dataset)
   - Aeromonas: Bacterial diseases - Aeromoniasis + Bacterial Red disease
   - Jamur: Fungal diseases Saprolegniasis
   - Parasit: Parasitic diseases
   - Sehat: Healthy Fish
2. Video Budidaya Lele YouTube (ID: DChp7FWb9rc, 8gwkTmkuOa4)
   - Overfeeding: Perut buncit / kembung akibat pakan berlebih
"""

import os
import io
import sys
import shutil
import hashlib
import zipfile
from pathlib import Path
from PIL import Image
import requests
import yt_dlp
import cv2

DATASET_ROOT = Path(r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele\dataset\fish_disease")
TARGET_CLASSES = ["Aeromonas", "Jamur", "Parasit", "Overfeeding", "Sehat"]

print("=" * 70)
print("  PIPELINE AKUISISI DATASET BARU SESUAI SUMBER DOKUMENTASI")
print("=" * 70)

# 1. Bersihkan seluruh folder dataset lama
print("\n[LANGKAH 1/4] Mengosongkan folder dataset lama...")
for cls in TARGET_CLASSES:
    folder = DATASET_ROOT / cls
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("*.*"):
        if f.name != ".gitkeep":
            try:
                f.unlink()
            except Exception:
                pass
print("  Folder dataset telah dikosongkan.")

# 2. Unduh dan ekstrak dari Kaggle rukesh17/cleaned-fish-disease-dataset
print("\n[LANGKAH 2/4] Mengunduh dataset penyakit ikan dari Kaggle (rukesh17)...")
kaggle_api_url = "https://www.kaggle.com/api/v1/datasets/download/rukesh17/cleaned-fish-disease-dataset"
resp = requests.get(kaggle_api_url, allow_redirects=False)
if resp.status_code != 302 or "Location" not in resp.headers:
    raise RuntimeError(f"Gagal mendapatkan URL unduhan Kaggle. Status: {resp.status_code}")

storage_url = resp.headers["Location"]
print("  Mengunduh arsip zip dataset...")
dl_resp = requests.get(storage_url, stream=True)
if dl_resp.status_code != 200:
    raise RuntimeError(f"Gagal mengunduh arsip zip. Status: {dl_resp.status_code}")

zip_bytes = io.BytesIO(dl_resp.content)
zf = zipfile.ZipFile(zip_bytes)
print(f"  Arsip zip berhasil dimuat ({len(zf.namelist())} file di dalam arsip).")

KAGGLE_MAPPING = {
    "Bacterial diseases - Aeromoniasis": "Aeromonas",
    "Bacterial Red disease": "Aeromonas",
    "Fungal diseases Saprolegniasis": "Jamur",
    "Parasitic diseases": "Parasit",
    "Healthy Fish": "Sehat",
}

kaggle_counts = {c: 0 for c in TARGET_CLASSES}
# Hanya ambil dari subfolder Train, Valid, Test asli (bukan Train_Augmented)
for fname in zf.namelist():
    if not (fname.endswith(".jpg") or fname.endswith(".png") or fname.endswith(".jpeg")):
        continue
    # Lewati folder augmentasi buatan jika ingin data orisinil
    parts = fname.split("/")
    if len(parts) < 3:
        continue
    split_dir = parts[1] # Train, Valid, Test, Train_Augmented
    if split_dir not in ["Train", "Valid", "Test"]:
        continue
    category_name = parts[2]
    
    if category_name in KAGGLE_MAPPING:
        target_cls = KAGGLE_MAPPING[category_name]
        try:
            img_data = zf.read(fname)
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            if img.width >= 50 and img.height >= 50:
                kaggle_counts[target_cls] += 1
                out_path = DATASET_ROOT / target_cls / f"raw_kaggle_{kaggle_counts[target_cls]:05d}.jpg"
                img.save(out_path, format="JPEG", quality=95)
        except Exception:
            continue

print("  Hasil ekstraksi dari Kaggle:")
for c, cnt in kaggle_counts.items():
    if cnt > 0:
        print(f"    • {c:<12}: {cnt} citra orisinil")

# 3. Ekstraksi Kelas Overfeeding dari Video YouTube Budidaya Lele
print("\n[LANGKAH 3/4] Ekstraksi citra Overfeeding dari video budidaya lele YouTube...")
video_urls = [
    ("https://www.youtube.com/watch?v=DChp7FWb9rc", "overfeed_vid1.mp4"),
    ("https://www.youtube.com/watch?v=8gwkTmkuOa4", "overfeed_vid2.mp4")
]

overfeed_folder = DATASET_ROOT / "Overfeeding"
overfeed_count = 0

for url, out_name in video_urls:
    print(f"  Mengunduh video: {url} ...")
    ydl_opts = {
        'format': '134/133/160/bestvideo',
        'outtmpl': out_name,
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(out_name):
            cap = cv2.VideoCapture(out_name)
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            # Ambil frame setiap 0.5 detik
            step = max(1, fps // 2)
            
            frame_num = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_num % step == 0:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    overfeed_count += 1
                    out_f = overfeed_folder / f"raw_vid_{overfeed_count:05d}.jpg"
                    pil_img.save(out_f, format="JPEG", quality=95)
                frame_num += 1
            
            cap.release()
            os.remove(out_name)
            print(f"    Ekstraksi selesai ({overfeed_count} frame tersimpan sejauh ini).")
    except Exception as e:
        print(f"    Gagal memproses video {url}: {e}")
        if os.path.exists(out_name):
            os.remove(out_name)

# 4. Cleaning, Deduplikasi & Standarisasi Citra
print("\n[LANGKAH 4/4] Menjalankan pembersihan menyeluruh (Cleaning, Deduplikasi & Naming)...")
seen_hashes = set()
final_report = {}

for cls in TARGET_CLASSES:
    folder = DATASET_ROOT / cls
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
                hsh = hashlib.md5(img.tobytes()).hexdigest()
                if hsh in seen_hashes:
                    f.unlink()
                    continue
                seen_hashes.add(hsh)
                kept_images.append(img.copy())
            f.unlink()
        except Exception:
            try:
                f.unlink()
            except Exception:
                pass
    
    # Simpan kembali dengan nama standar: [kelas]_[nomor].jpg
    for i, img in enumerate(kept_images, start=1):
        clean_file = folder / f"{cls.lower()}_{i:04d}.jpg"
        img.save(clean_file, format="JPEG", quality=95)
    
    final_count = len(list(folder.glob("*.jpg")))
    final_report[cls] = final_count
    print(f"  • {cls:<15}: {final_count} citra bersih siap latih")

print("\n" + "=" * 70)
print("  REKAP AKHIR DATASET RESMI DARI SUMBER DOKUMENTASI:")
total_all = sum(final_report.values())
for cls, cnt in final_report.items():
    print(f"    - {cls:<14}: {cnt} gambar")
print(f"  TOTAL KESELURUHAN : {total_all} gambar")
print("=" * 70)

