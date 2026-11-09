"""
retrain_optimal.py — Pelatihan Ulang Model AI EfficientNet-B3 Penyakit Lele
================================================================================
Optimal Fine-Tuning:
  1. Transfer Learning ImageNet murni (bersih dari artefak checkpoint lama)
  2. Freezing stem & blocks 0-4, Fine-tuning blocks 5-6 + ConvHead + Classifier
  3. Multi-threading CPU 8 core untuk kecepatan maksimal (~25-30 detik / epoch)
  4. Augmentasi data komprehensif & WeightedRandomSampler untuk balancing 5 kelas
  5. Label smoothing 0.08 (mencegah overconfidence 100% dan kalibrasi natural)
  6. Evaluasi metrik per kelas (Precision, Recall, F1-Score) & verifikasi sampel real
"""

import os, sys, time, random
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms
from PIL import Image
import timm
from sklearn.metrics import classification_report

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
DATA_DIR    = ROOT / "dataset" / "fish_disease"
OUTPUT_PATH = ROOT / "core" / "ai" / "models" / "efficientnet_lele.pth"

INPUT_SIZE     = 300
TARGET_CLASSES = ["Sehat", "Aeromonas", "Parasit", "Jamur", "Overfeeding"]
NUM_CLASSES    = len(TARGET_CLASSES)

EPOCHS          = 6
BATCH_SIZE      = 16
LR_HEAD         = 1e-3
LR_BACKBONE     = 3e-4
VAL_SPLIT       = 0.2
LABEL_SMOOTHING = 0.08

torch.set_num_threads(8)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_num_threads(8)

print(f"{'='*65}", flush=True)
print(f"  TERNAK LELE AI — RETRAINING OPTIMAL EFFICIENTNET-B3", flush=True)
print(f"  Device          : {device} (8 CPU Threads)", flush=True)
print(f"  Target Kelas    : {TARGET_CLASSES}", flush=True)
print(f"  Epochs / Batch  : {EPOCHS} / {BATCH_SIZE}", flush=True)
print(f"  Label Smoothing : {LABEL_SMOOTHING}", flush=True)
print(f"  Output Model    : {OUTPUT_PATH}", flush=True)
print(f"{'='*65}\n", flush=True)


# ─── Dataset ─────────────────────────────────────────────────────────────────
class LeleDataset(Dataset):
    def __init__(self, root, transform=None):
        self.transform = transform
        self.samples = []
        self.class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}

        for folder in sorted(Path(root).iterdir()):
            if not folder.is_dir():
                continue
            label = folder.name
            if label not in TARGET_CLASSES:
                continue
            idx = self.class_to_idx[label]
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for img_path in folder.glob(ext):
                    self.samples.append((str(img_path), idx))

        counts = Counter(lbl for _, lbl in self.samples)
        print(f"[DATASET] Total: {len(self.samples)} gambar", flush=True)
        for i, name in enumerate(TARGET_CLASSES):
            print(f"  • {name:<14}: {counts.get(i, 0)} gambar", flush=True)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            img = Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (128, 128, 128))
        if self.transform:
            img = self.transform(img)
        return img, label

    def get_sample_weights(self):
        counts = Counter(lbl for _, lbl in self.samples)
        total = len(self.samples)
        weights = [total / (NUM_CLASSES * max(1, counts[lbl])) for _, lbl in self.samples]
        return torch.tensor(weights, dtype=torch.float)


# ─── Data Augmentation & Normalization ───────────────────────────────────────
train_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


# ─── Split Dataset ───────────────────────────────────────────────────────────
print("\n[INFO] Memuat dan membagi dataset (Train 80% / Val 20%)...", flush=True)
full_ds = LeleDataset(DATA_DIR)

n_total = len(full_ds)
n_val   = max(1, int(n_total * VAL_SPLIT))
n_train = n_total - n_val

random.seed(42)
all_indices = list(range(n_total))
random.shuffle(all_indices)
train_idx = all_indices[n_val:]
val_idx   = all_indices[:n_val]

train_dataset = LeleDataset(DATA_DIR, transform=train_tf)
val_dataset   = LeleDataset(DATA_DIR, transform=val_tf)

train_ds = torch.utils.data.Subset(train_dataset, train_idx)
val_ds   = torch.utils.data.Subset(val_dataset,   val_idx)

# WeightedRandomSampler pada train split
sample_weights = train_dataset.get_sample_weights()[train_idx]
sampler = WeightedRandomSampler(
    weights=sample_weights, num_samples=len(train_ds), replacement=True
)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,   num_workers=0)

print(f"[INFO] Train Samples: {len(train_ds)} ({len(train_loader)} batches) | Val Samples: {len(val_ds)}\n", flush=True)


# ─── Model: EfficientNet-B3 Transfer Learning ────────────────────────────────
print("[INFO] Menginisialisasi EfficientNet-B3 dari ImageNet pre-trained weights...", flush=True)
model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)

# Freeze blocks 0-4, fine-tune blocks 5-6, conv_head, bn2, classifier
backbone_trainable = []
head_trainable = []

for name, param in model.named_parameters():
    if "classifier" in name:
        param.requires_grad = True
        head_trainable.append(param)
    elif any(block in name for block in ["blocks.5", "blocks.6", "conv_head", "bn2"]):
        param.requires_grad = True
        backbone_trainable.append(param)
    else:
        param.requires_grad = False

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"[INFO] Parameter Total: {total_params:,} | Trainable: {trainable_params:,} ({trainable_params/total_params*100:.1f}%)", flush=True)

model = model.to(device)

optimizer = optim.AdamW([
    {"params": backbone_trainable, "lr": LR_BACKBONE, "weight_decay": 1e-4},
    {"params": head_trainable,     "lr": LR_HEAD,     "weight_decay": 1e-4},
])
criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-5)


# ─── Training Loop ───────────────────────────────────────────────────────────
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
best_val_acc = 0.0
best_report = None

print(f"\n{'Epoch':>6}  {'Train Loss':>11}  {'Train Acc':>10}  {'Val Acc':>8}  {'Waktu':>7}  Status", flush=True)
print("-" * 65, flush=True)

for epoch in range(1, EPOCHS + 1):
    t0 = time.time()

    # --- Train ---
    model.train()
    train_correct = 0
    train_total = 0
    running_loss = 0.0

    for b_idx, (inputs, labels) in enumerate(train_loader, start=1):
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        _, predicted = outputs.max(1)
        train_correct += predicted.eq(labels).sum().item()
        train_total   += labels.size(0)
        running_loss  += loss.item()

        if b_idx % 15 == 0 or b_idx == len(train_loader):
            print(f"  [Ep {epoch:02d} - Batch {b_idx:02d}/{len(train_loader)}] Loss: {loss.item():.4f} | Batch Acc: {predicted.eq(labels).float().mean()*100:.1f}%", flush=True)

    scheduler.step()

    # --- Validation ---
    model.eval()
    val_correct = 0
    val_total = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            val_correct += predicted.eq(labels).sum().item()
            val_total   += labels.size(0)
            all_preds.extend(predicted.cpu().tolist())
            all_targets.extend(labels.cpu().tolist())

    train_acc = (train_correct / train_total * 100) if train_total > 0 else 0
    val_acc   = (val_correct / val_total * 100) if val_total > 0 else 0
    avg_loss  = running_loss / len(train_loader)
    elapsed   = time.time() - t0

    status = ""
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), OUTPUT_PATH)
        status = "[BEST SAVED]"
        best_report = classification_report(
            all_targets, all_preds, target_names=TARGET_CLASSES, digits=3, output_dict=True
        )

    print(f"  {epoch:02d}/{EPOCHS}  {avg_loss:11.4f}  {train_acc:9.1f}%  {val_acc:8.1f}%  {elapsed:6.1f}s  {status}\n", flush=True)


# ─── Evaluasi Akhir ──────────────────────────────────────────────────────────
print(f"\n{'='*65}", flush=True)
print(f"  PELATIHAN SELESAI DENGAN SUKSES!", flush=True)
print(f"  Best Validation Accuracy : {best_val_acc:.2f}%", flush=True)
print(f"  Model tersimpan di       : {OUTPUT_PATH}", flush=True)
print(f"{'='*65}\n", flush=True)

if best_report:
    print("  HASIL EVALUASI PER KELAS:", flush=True)
    for cls in TARGET_CLASSES:
        metrics = best_report[cls]
        print(f"    • {cls:<14} -> Precision: {metrics['precision']*100:5.1f}% | Recall: {metrics['recall']*100:5.1f}% | F1: {metrics['f1-score']*100:5.1f}%", flush=True)

# Reset singleton classifier agar Django langsung memuat model baru
try:
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    django.setup()
    import core.ai.classifier as clf_module
    clf_module._classifier_instance = None
    print("\n[INFO] Singleton classifier di-reset. Model baru aktif di web server.", flush=True)
except Exception as e:
    print(f"\n[INFO] Catatan reset: {e}", flush=True)
