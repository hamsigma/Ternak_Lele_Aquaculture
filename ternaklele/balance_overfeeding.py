"""
balance_overfeeding.py
Menyeimbangkan dataset Overfeeding dari 40 citra menjadi ~280 citra berkualitas tinggi
dengan augmentasi geometric, scaling/zoom perut, rotasi, dan subtle color variation.
"""
import os
import glob
from pathlib import Path
from PIL import Image, ImageEnhance
import random

ROOT = Path(__file__).resolve().parent
OVERFEEDING_DIR = ROOT / "dataset" / "fish_disease" / "Overfeeding"

# Kumpulkan citra asli (bukan hasil augmentasi sebelumnya)
original_files = [
    f for f in sorted(OVERFEEDING_DIR.glob("*.*"))
    if not f.name.startswith("aug_") and f.suffix.lower() in [".jpg", ".jpeg", ".png"]
]

print(f"[INFO] Ditemukan {len(original_files)} citra asli Overfeeding.")

aug_idx = 1
for img_path in original_files:
    try:
        with Image.open(img_path) as img:
            img = img.convert("RGB")
            w, h = img.size

            # 1. Horizontal Flip
            flip = img.transpose(Image.FLIP_LEFT_RIGHT)
            flip.save(OVERFEEDING_DIR / f"aug_overfeed_{aug_idx:04d}.jpg", quality=95)
            aug_idx += 1

            # 2. Zoom / Crop fokus ke perut (tengah 85%)
            crop_box = (int(w * 0.08), int(h * 0.08), int(w * 0.92), int(h * 0.92))
            crop_img = img.crop(crop_box).resize((w, h), Image.Resampling.LANCZOS)
            crop_img.save(OVERFEEDING_DIR / f"aug_overfeed_{aug_idx:04d}.jpg", quality=95)
            aug_idx += 1

            # 3. Zoom + Horizontal Flip
            crop_flip = flip.crop(crop_box).resize((w, h), Image.Resampling.LANCZOS)
            crop_flip.save(OVERFEEDING_DIR / f"aug_overfeed_{aug_idx:04d}.jpg", quality=95)
            aug_idx += 1

            # 4. Rotasi +7 derajat
            rot_p = img.rotate(7, resample=Image.Resampling.BILINEAR, fillcolor=(40, 50, 45))
            rot_p.save(OVERFEEDING_DIR / f"aug_overfeed_{aug_idx:04d}.jpg", quality=95)
            aug_idx += 1

            # 5. Rotasi -7 derajat
            rot_m = img.rotate(-7, resample=Image.Resampling.BILINEAR, fillcolor=(40, 50, 45))
            rot_m.save(OVERFEEDING_DIR / f"aug_overfeed_{aug_idx:04d}.jpg", quality=95)
            aug_idx += 1

            # 6. Variasi kontras dan kecerahan (simulasi pencahayaan kolam)
            enhancer = ImageEnhance.Contrast(img)
            enhanced = enhancer.enhance(1.1)
            enhancer_b = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer_b.enhance(0.95)
            enhanced.save(OVERFEEDING_DIR / f"aug_overfeed_{aug_idx:04d}.jpg", quality=95)
            aug_idx += 1

    except Exception as e:
        print(f"[WARN] Gagal augment {img_path.name}: {e}")

total_now = len(list(OVERFEEDING_DIR.glob("*.jpg")))
print(f"[SUCCESS] Total citra Overfeeding sekarang: {total_now} citra!")

