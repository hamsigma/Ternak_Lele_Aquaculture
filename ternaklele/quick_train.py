"""
Quick Training Script - Offline Mode (No Internet Required)
Menggunakan bobot lokal yang sudah ada, tidak perlu download dari HuggingFace.
Dioptimasi untuk CPU dengan batch kecil.

Usage:
    python quick_train.py
"""

import os
import time
import sys
from pathlib import Path

# Pastikan root ada di path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
import timm

# ─── Config ─────────────────────────────────────────────────────────────────
DATA_DIR    = ROOT / "dataset" / "fish_disease"
OUTPUT_PATH = ROOT / "core" / "ai" / "models" / "efficientnet_lele.pth"
EPOCHS      = 10       # cukup untuk baseline yang bisa detect
BATCH_SIZE  = 8        # kecil agar cepat di CPU
LR          = 1e-3
INPUT_SIZE  = 300      # disamakan ke 300 agar konsisten dengan classifier

TARGET_CLASSES = ["Sehat", "Aeromonas", "Malnutrisi", "Jamur", "Overfeeding"]
NUM_CLASSES    = len(TARGET_CLASSES)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n{'='*60}")
print(f"  Ternak Lele AI — Quick Training (Offline Mode)")
print(f"  Device  : {device}")
print(f"  Dataset : {DATA_DIR}")
print(f"  Epochs  : {EPOCHS}  |  Batch: {BATCH_SIZE}  |  LR: {LR}")
print(f"{'='*60}\n")


# ─── Dataset ─────────────────────────────────────────────────────────────────
class RemappedDataset(torch.utils.data.Dataset):
    LABEL_MAP = {
        "aeromoniasis":          "Aeromonas",
        "bacterial_red_disease": "Malnutrisi",
        "bacterial_gill":        "Malnutrisi",
        "saprolegniasis":        "Jamur",
        "fungal":                "Jamur",
        "parasitic":             "Overfeeding",
        "viral":                 "Overfeeding",
        "healthy":               "Sehat",
        "malnutrisi":            "Malnutrisi",
        "overfeeding":           "Overfeeding",
    }

    def __init__(self, root, transform=None):
        self.samples = []
        self.transform = transform
        self.class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}

        for folder in sorted(Path(root).iterdir()):
            if not folder.is_dir():
                continue
            label = self._remap(folder.name)
            if label is None:
                print(f"[WARN] Folder '{folder.name}' tidak dikenali, dilewati.")
                continue
            idx = self.class_to_idx[label]
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for img_path in folder.glob(ext):
                    self.samples.append((str(img_path), idx))

        print(f"[INFO] Total sampel ditemukan: {len(self.samples)}")

    def _remap(self, name):
        if name in TARGET_CLASSES:
            return name
        name_lower = name.lower()
        for key, target in self.LABEL_MAP.items():
            if key in name_lower:
                return target
        return None

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        from PIL import Image
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


train_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

full_dataset = RemappedDataset(DATA_DIR, transform=train_tf)

# Split 80/20
n_total = len(full_dataset)
n_val   = max(1, int(n_total * 0.2))
n_train = n_total - n_val
train_ds, val_ds = torch.utils.data.random_split(full_dataset, [n_train, n_val])

# Set val transform
val_ds.dataset = RemappedDataset(DATA_DIR, transform=val_tf)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                          num_workers=0, pin_memory=False)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                          num_workers=0, pin_memory=False)

print(f"[INFO] Train: {n_train} sampel | Val: {n_val} sampel\n")


# ─── Model ───────────────────────────────────────────────────────────────────
print("[INFO] Memuat model EfficientNet-B3 (offline, pretrained=False)...")
model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=NUM_CLASSES)

# Coba load bobot yang sudah ada jika tersedia
if OUTPUT_PATH.exists():
    print(f"[INFO] Memuat bobot awal dari: {OUTPUT_PATH}")
    try:
        state = torch.load(OUTPUT_PATH, map_location="cpu", weights_only=True)
        # Filter hanya key yang cocok (abaikan classifier head jika shape beda)
        model_state = model.state_dict()
        filtered = {
            k: v for k, v in state.items()
            if k in model_state and model_state[k].shape == v.shape
        }
        model.load_state_dict(filtered, strict=False)
        loaded = len(filtered)
        total  = len(model_state)
        print(f"[INFO] {loaded}/{total} layer berhasil dimuat dari checkpoint.")
    except Exception as e:
        print(f"[WARN] Gagal memuat checkpoint lama: {e}. Mulai dari bobot acak.")
else:
    print("[INFO] Tidak ada checkpoint awal. Mulai dari bobot acak.")

model = model.to(device)
print(f"[INFO] Model siap di {device}\n")


# ─── Loss & Optimizer ────────────────────────────────────────────────────────
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)


# ─── Training Loop ───────────────────────────────────────────────────────────
best_val_acc = 0.0
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

for epoch in range(1, EPOCHS + 1):
    t0 = time.time()

    # --- Train ---
    model.train()
    train_loss = train_correct = train_total = 0
    for batch_idx, (inputs, labels) in enumerate(train_loader):
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss    += loss.item() * inputs.size(0)
        _, predicted   = outputs.max(1)
        train_correct += predicted.eq(labels).sum().item()
        train_total   += labels.size(0)

        # Progress setiap 10 batch
        if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == len(train_loader):
            pct = (batch_idx + 1) / len(train_loader) * 100
            print(f"  Epoch {epoch:02d}/{EPOCHS} | Batch {batch_idx+1:3d}/{len(train_loader)} "
                  f"[{pct:.0f}%] | Loss: {loss.item():.4f}", end="\r")

    # --- Val ---
    model.eval()
    val_loss = val_correct = val_total = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            val_loss    += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            val_correct += predicted.eq(labels).sum().item()
            val_total   += labels.size(0)

    scheduler.step()

    train_acc = train_correct / train_total * 100
    val_acc   = val_correct   / val_total   * 100
    elapsed   = time.time() - t0

    print(f"\nEpoch [{epoch:02d}/{EPOCHS}] "
          f"Train Loss: {train_loss/train_total:.4f} Acc: {train_acc:.1f}% | "
          f"Val Loss: {val_loss/val_total:.4f} Acc: {val_acc:.1f}% | "
          f"Time: {elapsed:.1f}s")

    # Simpan model terbaik
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), OUTPUT_PATH)
        print(f"  [SAVED] Model terbaik disimpan! Val Acc: {val_acc:.1f}%")


# ─── Ringkasan Akhir ─────────────────────────────────────────────────────────
print(f"\n{'='*60}")
if best_val_acc >= 70.0:
    print(f"  [SUKSES] Training selesai! Best Val Acc: {best_val_acc:.1f}%")
    print(f"  Model disimpan di: {OUTPUT_PATH}")
else:
    print(f"  [SELESAI] Best Val Acc: {best_val_acc:.1f}%")
    print(f"  Tip: Jalankan dengan --epochs lebih banyak untuk akurasi lebih tinggi.")
print(f"{'='*60}\n")

# Reset singleton classifier
try:
    import core.ai.classifier as clf_module
    clf_module._classifier_instance = None
    print("[INFO] Classifier singleton direset — model baru aktif saat deteksi berikutnya.")
except Exception:
    pass
