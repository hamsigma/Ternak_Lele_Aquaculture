"""
train_deep_patterns.py
================================================================================
Melatih model EfficientNet-B3 untuk mengenali pola visual spesifik penyakit ikan lele:
- Aeromonas: Luka borok kemerahan, bintik hemoragi, sirip nekrotik.
- Jamur: Hifa kapas putih/keabuan (Saprolegnia).
- Parasit: Bintik putih diskrit (White Spot / Ich), cacing jangkar.
- Overfeeding: Kontur perut membuncit bulat padat tanpa luka terbuka.
- Sehat: Kulit licin merata, sungut utuh tegang, postur tubuh simetris.

Strategi Pelatihan:
1. Feature caching dari Blocks 0-5 (inference mode, 8 CPU threads, sangat cepat).
2. Fine-tuning end-to-end pada Block 6 (3.28M params) + Conv Head (590K params) + Classifier.
3. Weighted Random Sampling & Label Smoothing 0.05 untuk kalibrasi keyakinan optimal.
================================================================================
"""

import os
import sys
import time
import random
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from torchvision import transforms
from PIL import Image
import timm
from sklearn.metrics import classification_report

torch.set_num_threads(8)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DATA_DIR    = ROOT / "dataset" / "fish_disease"
OUTPUT_PATH = ROOT / "core" / "ai" / "models" / "efficientnet_lele.pth"

INPUT_SIZE     = 300
TARGET_CLASSES = ["Sehat", "Aeromonas", "Parasit", "Jamur", "Overfeeding"]
NUM_CLASSES    = len(TARGET_CLASSES)
LABEL_SMOOTHING = 0.05

print("=" * 70, flush=True)
print("  TERNAK LELE AI — DEEP PATTERN LEARNING (BLOCK 6 + HEAD TUNING)", flush=True)
print(f"  Device          : {device} (8 CPU Threads)", flush=True)
print(f"  Target Classes  : {TARGET_CLASSES}", flush=True)
print(f"  Model Output    : {OUTPUT_PATH}", flush=True)
print("=" * 70 + "\n", flush=True)

# ─── 1. Kumpulkan Sampel dari Dataset ─────────────────────────────────────────
print("[1/6] Memindai seluruh dataset...", flush=True)
class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}
all_samples = []

for folder in sorted(DATA_DIR.iterdir()):
    if not folder.is_dir() or folder.name not in TARGET_CLASSES:
        continue
    c_idx = class_to_idx[folder.name]
    for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
        for p in folder.glob(ext):
            all_samples.append((str(p), c_idx, p.name))

counts = Counter(lbl for _, lbl, _ in all_samples)
print(f"  Total Sampel Gambar: {len(all_samples)}")
for i, name in enumerate(TARGET_CLASSES):
    print(f"    • {name:<14}: {counts.get(i, 0)} gambar")

# ─── 2. Inisialisasi Backbone Pre-Trained ─────────────────────────────────────
print("\n[2/6] Memuat ImageNet Pre-Trained EfficientNet-B3...", flush=True)
full_model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)
full_model.eval()
full_model = full_model.to(device)

tf_orig = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

tf_flip = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(p=1.0),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ─── 3. Ekstraksi Fitur Spasial dari Blocks 0-5 ───────────────────────────────
print("\n[3/6] Mengekstrak aktivasi spasial dari Blocks 0-5 (Original + Flip)...", flush=True)
t_start = time.time()

spatial_list = []
labels_list = []

batch_imgs = []
batch_lbls = []
BATCH_EXTRACT = 32

def forward_blocks_0_to_5(model, x):
    h = model.conv_stem(x)
    h = model.bn1(h)
    for i in range(6):
        h = model.blocks[i](h)
    return h  # Shape: (B, 232, 10, 10)

with torch.inference_mode():
    for idx, (path, label, fname) in enumerate(all_samples, start=1):
        try:
            pil_img = Image.open(path).convert("RGB")
            t_orig = tf_orig(pil_img)
            t_flip = tf_flip(pil_img)

            batch_imgs.extend([t_orig, t_flip])
            batch_lbls.extend([label, label])

            if len(batch_imgs) >= BATCH_EXTRACT or idx == len(all_samples):
                inp = torch.stack(batch_imgs).to(device)
                h_early = forward_blocks_0_to_5(full_model, inp).cpu()
                spatial_list.append(h_early)
                labels_list.extend(batch_lbls)

                batch_imgs = []
                batch_lbls = []

            if idx % 250 == 0 or idx == len(all_samples):
                print(f"  Diproses: {idx}/{len(all_samples)} gambar ({time.time()-t_start:.1f}s)", flush=True)

        except Exception as e:
            print(f"  [WARN] Gagal membaca {path}: {e}")

X_spatial = torch.cat(spatial_list, dim=0)
y_all = torch.tensor(labels_list, dtype=torch.long)
print(f"  Ekstraksi Selesai! Tensor Shape: {X_spatial.shape} ({time.time()-t_start:.1f}s)\n", flush=True)

# ─── 4. Train / Validation Split ─────────────────────────────────────────────
print("[4/6] Membagi Train (80%) dan Validation (20%)...", flush=True)
N = len(X_spatial)
random.seed(42)
indices = list(range(N))
random.shuffle(indices)

n_val = int(N * 0.2)
val_idx = indices[:n_val]
train_idx = indices[n_val:]

X_train, y_train = X_spatial[train_idx], y_all[train_idx]
X_val, y_val     = X_spatial[val_idx], y_all[val_idx]

train_counts = Counter(y_train.tolist())
train_weights = [1.0 / (NUM_CLASSES * train_counts[lbl]) for lbl in y_train.tolist()]
sampler = WeightedRandomSampler(train_weights, num_samples=len(X_train), replacement=True)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, sampler=sampler)
val_loader   = DataLoader(TensorDataset(X_val, y_val), batch_size=32, shuffle=False)

print(f"  Train: {len(X_train)} sampel | Validation: {len(X_val)} sampel\n", flush=True)

# ─── 5. Model Sub-Network: Block 6 + Conv Head + Classifier ──────────────────
print("[5/6] Membangun Sub-Jaringan Pola Visual...", flush=True)

class PatternRecognitionHead(nn.Module):
    def __init__(self, block6, conv_head, bn2, global_pool, classifier):
        super().__init__()
        self.block6 = block6
        self.conv_head = conv_head
        self.bn2 = bn2
        self.global_pool = global_pool
        self.classifier = classifier

    def forward(self, x):
        h = self.block6(x)
        h = self.conv_head(h)
        h = self.bn2(h)
        h = self.global_pool(h)
        out = self.classifier(h)
        return out

pattern_net = PatternRecognitionHead(
    full_model.blocks[6],
    full_model.conv_head,
    full_model.bn2,
    full_model.global_pool,
    full_model.classifier
).to(device)

criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)

# Tahap 1: Latih Conv Head & Classifier terlebih dahulu (5 Epochs)
print("  -> Tahap 1: Pemanasan Conv Head & Classifier (5 Epochs)...", flush=True)
for p in pattern_net.block6.parameters():
    p.requires_grad = False
for p in pattern_net.conv_head.parameters():
    p.requires_grad = True
for p in pattern_net.bn2.parameters():
    p.requires_grad = True
for p in pattern_net.classifier.parameters():
    p.requires_grad = True

opt_stage1 = optim.AdamW(
    [p for p in pattern_net.parameters() if p.requires_grad],
    lr=1e-3, weight_decay=1e-4
)

for ep in range(1, 6):
    pattern_net.train()
    loss_sum = 0
    correct = 0
    total = 0
    for bx, by in train_loader:
        bx, by = bx.to(device), by.to(device)
        opt_stage1.zero_grad()
        out = pattern_net(bx)
        loss = criterion(out, by)
        loss.backward()
        opt_stage1.step()

        loss_sum += loss.item() * by.size(0)
        _, pred = out.max(1)
        correct += pred.eq(by).sum().item()
        total += by.size(0)

    print(f"     [Stage 1] Epoch {ep}/5 | Loss: {loss_sum/total:.4f} | Train Acc: {correct/total*100:.1f}%", flush=True)

# Tahap 2: Buka Block 6 untuk Fine-Tuning Pola Spasial (15 Epochs)
print("\n  -> Tahap 2: Fine-Tuning Pola Visual Spasial (Block 6 + Head, 15 Epochs)...", flush=True)
for p in pattern_net.block6.parameters():
    p.requires_grad = True

opt_stage2 = optim.AdamW([
    {"params": pattern_net.block6.parameters(), "lr": 1.5e-4},
    {"params": pattern_net.conv_head.parameters(), "lr": 3e-4},
    {"params": pattern_net.bn2.parameters(), "lr": 3e-4},
    {"params": pattern_net.classifier.parameters(), "lr": 5e-4},
], weight_decay=1e-4)

sched_stage2 = optim.lr_scheduler.CosineAnnealingLR(opt_stage2, T_max=15, eta_min=1e-5)

best_val_acc = 0.0
best_model_state = None
best_report = None

for ep in range(1, 16):
    pattern_net.train()
    loss_sum, correct, total = 0, 0, 0
    for bx, by in train_loader:
        bx, by = bx.to(device), by.to(device)
        opt_stage2.zero_grad()
        out = pattern_net(bx)
        loss = criterion(out, by)
        loss.backward()
        opt_stage2.step()

        loss_sum += loss.item() * by.size(0)
        _, pred = out.max(1)
        correct += pred.eq(by).sum().item()
        total += by.size(0)

    sched_stage2.step()

    # Evaluasi Val
    pattern_net.eval()
    val_correct, val_total = 0, 0
    all_preds, all_targets = [], []
    with torch.no_grad():
        for bx, by in val_loader:
            bx, by = bx.to(device), by.to(device)
            out = pattern_net(bx)
            _, pred = out.max(1)
            val_correct += pred.eq(by).sum().item()
            val_total += by.size(0)
            all_preds.extend(pred.cpu().tolist())
            all_targets.extend(by.cpu().tolist())

    val_acc = val_correct / val_total * 100
    train_acc = correct / total * 100

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model_state = {k: v.cpu().clone() for k, v in full_model.state_dict().items()}
        best_report = classification_report(all_targets, all_preds, target_names=TARGET_CLASSES, digits=3, output_dict=True)

    print(f"     [Stage 2] Epoch {ep:02d}/15 | Train: {train_acc:5.1f}% | Val: {val_acc:5.1f}% (Best: {best_val_acc:5.1f}%)", flush=True)

# ─── 6. Simpan Model & Verifikasi ────────────────────────────────────────────
print(f"\n{'='*70}", flush=True)
print(f"  HASIL AKHIR FINE-TUNING POLA PENYAKIT", flush=True)
print(f"  Best Validation Accuracy: {best_val_acc:.2f}%", flush=True)
print(f"{'='*70}\n", flush=True)

if best_report:
    print("  Laporan Evaluasi Per Kelas:", flush=True)
    for cls in TARGET_CLASSES:
        m = best_report[cls]
        print(f"    • {cls:<14} -> Precision: {m['precision']*100:5.1f}% | Recall: {m['recall']*100:5.1f}% | F1: {m['f1-score']*100:5.1f}%", flush=True)

# Simpan bobot terbaik ke file model resmi
if best_model_state is not None:
    full_model.load_state_dict(best_model_state)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
torch.save(full_model.state_dict(), OUTPUT_PATH)
print(f"\n[INFO] Model final lengkap berhasil disimpan ke: {OUTPUT_PATH}", flush=True)

# Reset singleton classifier Django
try:
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    django.setup()
    import core.ai.classifier as clf_module
    clf_module._classifier_instance = None
    print("[INFO] Singleton classifier di-reset untuk melayani inferensi di server.", flush=True)
except Exception as e:
    print(f"[INFO] Info reset: {e}", flush=True)

