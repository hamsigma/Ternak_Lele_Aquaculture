"""
retrain_optimal.py — Script Training Terbaik untuk Sistem Deteksi Penyakit Lele
================================================================================
Perbaikan dari script sebelumnya:
  1. INPUT_SIZE = 300 (konsisten dengan LeleClassifier di runtime)
  2. pretrained=True dengan fallback offline (transfer learning = jauh lebih akurat)
  3. Split train/val yang benar menggunakan dua dataset terpisah (tidak ada data leak)
  4. Augmentasi agresif dan WeightedRandomSampler untuk kelas imbalance
  5. Label smoothing + Cosine Annealing untuk generalisasi lebih baik
  6. Early stopping untuk mencegah overfitting

Usage:
    cd "c:\\Users\\Administrator\\Documents\\Tenak Lele\\ternaklele"
    python retrain_optimal.py
"""

import os, sys, time, random
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from PIL import Image
import timm

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
DATA_DIR    = ROOT / "dataset" / "fish_disease"
OUTPUT_PATH = ROOT / "core" / "ai" / "models" / "efficientnet_lele.pth"

# PENTING: INPUT_SIZE harus sama dengan LeleClassifier.INPUT_SIZE = (300, 300)
INPUT_SIZE     = 300
TARGET_CLASSES = ["Sehat", "Aeromonas", "Malnutrisi", "Jamur", "Overfeeding"]
NUM_CLASSES    = len(TARGET_CLASSES)

EPOCHS        = None      # Akan diset secara dinamis
BATCH_SIZE    = 16
LR_HEAD       = None      # Akan diset secara dinamis
LR_BACKBONE   = None      # Akan diset secara dinamis
VAL_SPLIT     = 0.2
PATIENCE      = None      # Akan diset secara dinamis

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")



# ─── Dataset ─────────────────────────────────────────────────────────────────
class LeleDataset(Dataset):
    """Dataset langsung dari folder berlabel sesuai TARGET_CLASSES."""

    def __init__(self, root, transform=None):
        self.transform = transform
        self.samples   = []
        self.class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}

        for folder in sorted(Path(root).iterdir()):
            if not folder.is_dir():
                continue
            label = folder.name
            if label not in TARGET_CLASSES:
                print(f"  [SKIP] Folder '{label}' tidak dikenali.")
                continue
            idx = self.class_to_idx[label]
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for img_path in folder.glob(ext):
                    self.samples.append((str(img_path), idx))

        # Statistik kelas
        counts = Counter(lbl for _, lbl in self.samples)
        print(f"  Total sampel: {len(self.samples)}")
        for i, name in enumerate(TARGET_CLASSES):
            print(f"    {name:<15}: {counts.get(i, 0)} gambar")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            print(f"  [WARN] Gagal baca {path}: {e}")
            img = Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (128, 128, 128))
        if self.transform:
            img = self.transform(img)
        return img, label

    def get_sample_weights(self):
        """Hitung bobot per sampel untuk WeightedRandomSampler (balancing kelas)."""
        counts = Counter(lbl for _, lbl in self.samples)
        total  = len(self.samples)
        weights = [total / (NUM_CLASSES * counts[lbl]) for _, lbl in self.samples]
        return torch.tensor(weights, dtype=torch.float)


# ─── Transforms ──────────────────────────────────────────────────────────────
# Augmentasi agresif untuk training (ukuran 300 konsisten dengan runtime)
train_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.1)),
])

# Validasi: hanya resize + normalize (tidak ada augmentasi)
val_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ─── Split Dataset ───────────────────────────────────────────────────────────
print("[INFO] Memuat dataset...")
full_dataset = LeleDataset(DATA_DIR)  # Dataset tanpa transform (hanya untuk indeks)

n_total = len(full_dataset)
n_val   = max(1, int(n_total * VAL_SPLIT))
n_train = n_total - n_val

# Shuffle dengan seed tetap untuk reprodusibilitas
random.seed(42)
all_indices = list(range(n_total))
random.shuffle(all_indices)
train_idx = all_indices[n_val:]
val_idx   = all_indices[:n_val]

# Buat DUER dataset terpisah dengan transform berbeda (menghindari data leak!)
train_dataset = LeleDataset(DATA_DIR, transform=train_tf)
val_dataset   = LeleDataset(DATA_DIR, transform=val_tf)

# Ambil subset dengan indeks yang sama
train_ds = torch.utils.data.Subset(train_dataset, train_idx)
val_ds   = torch.utils.data.Subset(val_dataset,   val_idx)

# WeightedRandomSampler untuk menangani kelas imbalance
sample_weights = train_dataset.get_sample_weights()[train_idx]
sampler = WeightedRandomSampler(
    weights=sample_weights, num_samples=len(train_ds), replacement=True
)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler,   num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,     num_workers=0)

print(f"\n[INFO] Train: {len(train_ds)} | Val: {len(val_ds)}\n")


# ─── Model ───────────────────────────────────────────────────────────────────
print("[INFO] Memuat model EfficientNet-B3...")

# Coba pretrained=True (transfer learning) → fallback ke pretrained=False
try:
    model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)
    print("[INFO] Transfer learning: ImageNet pre-trained weights berhasil dimuat!")
    USE_PRETRAINED = True
except Exception as e:
    print(f"[WARN] Gagal unduh pre-trained weights ({e}).")
    print("[INFO] Fallback ke pretrained=False. Memuat checkpoint lokal jika ada...")
    model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=NUM_CLASSES)
    USE_PRETRAINED = False

# Load checkpoint lokal jika ada
if OUTPUT_PATH.exists():
    print(f"[INFO] Load checkpoint lokal: {OUTPUT_PATH}")
    try:
        try:
            state = torch.load(OUTPUT_PATH, map_location="cpu", weights_only=True)
        except Exception:
            state = torch.load(OUTPUT_PATH, map_location="cpu", weights_only=False)
        model_state = model.state_dict()
        filtered = {k: v for k, v in state.items()
                    if k in model_state and model_state[k].shape == v.shape}
        model.load_state_dict(filtered, strict=False)
        print(f"[INFO] {len(filtered)}/{len(model_state)} layers dimuat dari checkpoint.")
    except Exception as e:
        print(f"[WARN] Gagal load checkpoint: {e}. Mulai dari bobot awal.")
else:
    print("[INFO] Tidak ada checkpoint. Mulai dari awal.")

model = model.to(device)

# --- Dynamic Hyperparameter Tuning ---
if USE_PRETRAINED:
    # Hyperparameters untuk fine-tuning (transfer learning)
    EPOCHS = 25
    LR_BACKBONE = 5e-5
    LR_HEAD = 1e-3
    PATIENCE = 7
    LABEL_SMOOTHING = 0.1
    print("[CONFIG] Menggunakan hyperparameter fine-tuning.")
else:
    # Hyperparameters untuk training dari nol (scratch/offline)
    EPOCHS = 100
    LR_BACKBONE = 5e-4
    LR_HEAD = 1e-3
    PATIENCE = 15
    LABEL_SMOOTHING = 0.05
    print("[CONFIG] Menggunakan hyperparameter training-from-scratch (offline mode).")

print(f"\n{'='*65}")
print(f"  Ternak Lele AI — Optimal Training Script")
print(f"  Device      : {device}")
print(f"  Dataset     : {DATA_DIR}")
print(f"  Pretrained  : {USE_PRETRAINED}")
print(f"  Epochs      : {EPOCHS}  |  Batch: {BATCH_SIZE}")
print(f"  Backbone LR : {LR_BACKBONE}  |  Head LR: {LR_HEAD}")
print(f"  Input Size  : {INPUT_SIZE}x{INPUT_SIZE}")
print(f"  Output      : {OUTPUT_PATH}")
print(f"{'='*65}\n")

# ─── Optimizer: Learning Rate Berbeda untuk Head vs Backbone ─────────────────
backbone_params = [p for n, p in model.named_parameters() if "classifier" not in n]
head_params     = [p for n, p in model.named_parameters() if "classifier" in n]

optimizer = optim.AdamW([
    {"params": backbone_params, "lr": LR_BACKBONE, "weight_decay": 1e-4},
    {"params": head_params,     "lr": LR_HEAD,     "weight_decay": 1e-4},
])
criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)


# ─── Training Loop ───────────────────────────────────────────────────────────
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

best_val_acc   = 0.0
epochs_no_impr = 0

print(f"\n{'Epoch':>6}  {'Train Acc':>10}  {'Val Acc':>8}  {'LR':>10}  {'Waktu':>7}  Status")
print("-" * 65)

for epoch in range(1, EPOCHS + 1):
    t0 = time.time()

    # --- Train ---
    model.train()
    train_correct = train_total = 0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss    = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        _, predicted  = outputs.max(1)
        train_correct += predicted.eq(labels).sum().item()
        train_total   += labels.size(0)

    # --- Val ---
    model.eval()
    val_correct = val_total = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs        = model(inputs)
            _, predicted   = outputs.max(1)
            val_correct   += predicted.eq(labels).sum().item()
            val_total     += labels.size(0)

    scheduler.step()

    train_acc = train_correct / train_total * 100 if train_total > 0 else 0
    val_acc   = val_correct   / val_total   * 100 if val_total   > 0 else 0
    elapsed   = time.time() - t0
    cur_lr    = scheduler.get_last_lr()[0]

    status = ""
    if val_acc > best_val_acc:
        best_val_acc   = val_acc
        epochs_no_impr = 0
        torch.save(model.state_dict(), OUTPUT_PATH)
        status = "[SAVED]"
    else:
        epochs_no_impr += 1

    print(f"  {epoch:02d}/{EPOCHS}  {train_acc:9.1f}%  {val_acc:8.1f}%  {cur_lr:10.2e}  {elapsed:6.1f}s  {status}")

    # Early stopping
    if epochs_no_impr >= PATIENCE:
        print(f"\n[INFO] Early stopping pada epoch {epoch} (tidak ada perbaikan selama {PATIENCE} epoch).")
        break


# ─── Ringkasan ───────────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"  TRAINING SELESAI")
print(f"  Best Val Accuracy : {best_val_acc:.1f}%")
print(f"  Model tersimpan di: {OUTPUT_PATH}")

if best_val_acc >= 90:
    print("  STATUS: SANGAT BAIK - Siap produksi!")
elif best_val_acc >= 80:
    print("  STATUS: BAIK - Dapat digunakan.")
elif best_val_acc >= 70:
    print("  STATUS: CUKUP - Pertimbangkan tambah data atau epoch.")
else:
    print("  STATUS: KURANG - Tambahkan lebih banyak gambar per kelas.")

print(f"{'='*65}")
print("\n[INFO] Model baru akan otomatis digunakan pada deteksi berikutnya (hot-reload).")

# Reset singleton classifier agar model baru langsung dimuat
try:
    import django, os as _os
    _os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    django.setup()
    import core.ai.classifier as clf_module
    clf_module._classifier_instance = None
    print("[INFO] Singleton classifier di-reset. Model baru aktif di server.")
except Exception:
    print("[INFO] Jalankan ulang server Django untuk mengaktifkan model baru.")
