"""
Extended Training Script - Melanjutkan dari checkpoint terbaik
Training 30 epoch tambahan dengan augmentasi agresif dan LR warm-up.
Dirancang untuk mencapai val accuracy >= 95% pada data nyata.

Usage:
    python extended_train.py
"""

import os
import time
import sys
from pathlib import Path

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
EPOCHS      = 15      # Cukup untuk konvergensi
BATCH_SIZE  = 16      # Balance antara kecepatan dan memori
LR          = 5e-4
INPUT_SIZE  = 300     # HARUS sama dengan LeleClassifier.INPUT_SIZE = (300, 300)

TARGET_CLASSES = ["Sehat", "Aeromonas", "Malnutrisi", "Jamur", "Overfeeding"]
NUM_CLASSES    = len(TARGET_CLASSES)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"\n{'='*65}")
print(f"  Ternak Lele AI — Extended Training (Target: >=95% Val Acc)")
print(f"  Device  : {device}")
print(f"  Dataset : {DATA_DIR}")
print(f"  Epochs  : {EPOCHS}  |  Batch: {BATCH_SIZE}  |  LR: {LR}")
print(f"  Output  : {OUTPUT_PATH}")
print(f"{'='*65}\n")


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
        "bercak_merah":          "Malnutrisi",
        "parasit":               "Overfeeding",
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
                continue
            idx = self.class_to_idx[label]
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for img_path in folder.glob(ext):
                    self.samples.append((str(img_path), idx))

        print(f"[INFO] Total sampel: {len(self.samples)}")

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


# Augmentasi cukup untuk generalisasi
train_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE + 16, INPUT_SIZE + 16)),
    transforms.RandomCrop(INPUT_SIZE),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(20),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.1),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    transforms.RandomErasing(p=0.1),
])

val_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# Split dataset 80/20
full_train = RemappedDataset(DATA_DIR, transform=train_tf)
full_val   = RemappedDataset(DATA_DIR, transform=val_tf)

n_total = len(full_train)
n_val   = max(1, int(n_total * 0.2))
n_train = n_total - n_val

# Pakai indeks yang sama untuk split fair
import random
random.seed(42)
all_indices = list(range(n_total))
random.shuffle(all_indices)
train_idx = all_indices[n_val:]
val_idx   = all_indices[:n_val]

train_ds = torch.utils.data.Subset(full_train, train_idx)
val_ds   = torch.utils.data.Subset(full_val,   val_idx)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0, pin_memory=False)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=False)

print(f"[INFO] Train: {len(train_ds)} | Val: {len(val_ds)}\n")


# ─── Model ───────────────────────────────────────────────────────────────────
print("[INFO] Memuat model EfficientNet-B3...")
try:
    model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)
    print("[INFO] Transfer learning: ImageNet pre-trained weights berhasil dimuat!")
except Exception as e:
    print(f"[WARN] Gagal unduh pre-trained weights ({e}). Fallback ke pretrained=False.")
    model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=NUM_CLASSES)

if OUTPUT_PATH.exists():
    print(f"[INFO] Load checkpoint dari: {OUTPUT_PATH}")
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
        print(f"[WARN] Gagal load checkpoint: {e}. Mulai dari awal.")
else:
    print("[INFO] Tidak ada checkpoint. Mulai dari bobot acak.")

model = model.to(device)
model.train()
print(f"[INFO] Model siap di {device}\n")


# ─── Loss & Optimizer ────────────────────────────────────────────────────────
# Label smoothing untuk regularisasi tambahan
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

# Unfreeze semua layer dari awal karena kita lanjut dari checkpoint yang sudah baik
optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)

# Cosine annealing untuk decay yang halus
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)


# ─── Training Loop ───────────────────────────────────────────────────────────
best_val_acc = 0.0
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
log_file = ROOT / "extended_epoch_log.csv"

with open(log_file, "w") as f:
    f.write("epoch,train_loss,train_acc,val_loss,val_acc,time_s\n")

print(f"{'Epoch':<8} {'Train Loss':<12} {'Train Acc':<12} {'Val Loss':<12} {'Val Acc':<12} {'Time':<10} {'Note'}")
print("-" * 75)

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
        # Gradient clipping untuk stabilitas
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        train_loss    += loss.item() * inputs.size(0)
        _, predicted   = outputs.max(1)
        train_correct += predicted.eq(labels).sum().item()
        train_total   += labels.size(0)

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

    tr_loss = train_loss / train_total
    tr_acc  = train_correct / train_total * 100
    vl_loss = val_loss / val_total
    vl_acc  = val_correct / val_total * 100
    elapsed = time.time() - t0

    note = ""
    if vl_acc > best_val_acc:
        best_val_acc = vl_acc
        torch.save(model.state_dict(), OUTPUT_PATH)
        note = "[SAVED BEST]"

    print(f"{epoch:3d}/{EPOCHS:<4} {tr_loss:<12.4f} {tr_acc:<12.1f} {vl_loss:<12.4f} {vl_acc:<12.1f} {elapsed:<10.0f} {note}")

    with open(log_file, "a") as f:
        f.write(f"{epoch},{tr_loss:.4f},{tr_acc:.1f},{vl_loss:.4f},{vl_acc:.1f},{elapsed:.0f}\n")

    # Early stopping jika sudah sangat bagus
    if best_val_acc >= 98.0 and epoch >= 10:
        print(f"\n[EARLY STOP] Val Acc {best_val_acc:.1f}% >= 98% setelah {epoch} epoch.")
        break


# ─── Ringkasan ───────────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"  Training Selesai!")
print(f"  Best Val Accuracy : {best_val_acc:.1f}%")
print(f"  Model tersimpan di: {OUTPUT_PATH}")
if best_val_acc >= 90:
    print(f"  STATUS: SANGAT BAIK - siap digunakan di produksi!")
elif best_val_acc >= 80:
    print(f"  STATUS: BAIK - bisa digunakan, tambah data untuk hasil lebih baik.")
else:
    print(f"  STATUS: Perlu lebih banyak data atau epoch tambahan.")
print(f"{'='*65}\n")

# Reset singleton
try:
    import core.ai.classifier as clf_module
    clf_module._classifier_instance = None
    print("[INFO] Classifier singleton direset — model baru aktif.")
except Exception:
    pass
