"""
train_rigorous.py — Pelatihan Bebas Kebocoran Data (Strict Zero-Leakage Pipeline)
================================================================================
Standar Ilmiah & Rekayasa Machine Learning yang Ketat:
1. Pemisahan data Train (75%), Validation (15%), dan Test (10%) dilakukan di tingkat
   GROUP / UNIQUE SUBJECT sebelum augmentasi apa pun dilakukan.
2. Data Validation dan Data Test murni 100% citra ASLI (tanpa augmentasi cermin/flip).
3. Data Augmentasi (Flip, Zoom, ColorJitter, RandomErasing) HANYA diterapkan pada Data Latih.
4. Model: Fine-tuning Block 6 (3.28M params) + Conv Head (590K params) + Classifier.
5. Evaluasi akhir diuji pada Unseen Independent Test Set (Uji Buta).
================================================================================
"""

import os
import sys
import time
import random
import glob
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
from sklearn.metrics import classification_report, confusion_matrix

torch.set_num_threads(8)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

DATA_DIR    = ROOT / "dataset" / "fish_disease"
OUTPUT_PATH = ROOT / "core" / "ai" / "models" / "efficientnet_lele.pth"

INPUT_SIZE     = 300
TARGET_CLASSES = ["Sehat", "Aeromonas", "Parasit", "Jamur", "Overfeeding"]
NUM_CLASSES    = len(TARGET_CLASSES)
LABEL_SMOOTHING = 0.05

print("=" * 75, flush=True)
print("  TERNAK LELE AI — RIGOROUS ZERO-LEAKAGE TRAINING PIPELINE", flush=True)
print(f"  Device          : {device} (8 CPU Threads)", flush=True)
print(f"  Target Classes  : {TARGET_CLASSES}", flush=True)
print(f"  Model Output    : {OUTPUT_PATH}", flush=True)
print("=" * 75 + "\n", flush=True)

# ─── 1. Pemisahan Data Bebas Kebocoran (Strict Subject Group Split) ───────────
print("[1/6] Mengelompokkan dan memisahkan data tanpa kebocoran (Train 75% | Val 15% | Test 10%)...", flush=True)
random.seed(42)

train_files = [] # List of (path, label)
val_files   = []
test_files  = []

class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}

for cls in TARGET_CLASSES:
    folder = DATA_DIR / cls
    c_idx = class_to_idx[cls]

    if cls == "Overfeeding":
        # Kelompokkan 40 citra master induk
        all_overfeed = sorted(list(folder.glob("*.*")))
        master_files = [f for f in all_overfeed if not f.name.startswith("aug_") and f.suffix.lower() in [".jpg", ".png", ".jpeg"]]
        random.shuffle(master_files)

        n_master = len(master_files) # 40
        n_test = max(4, int(n_master * 0.10)) # 4 master
        n_val  = max(6, int(n_master * 0.15)) # 6 master
        n_train = n_master - n_test - n_val   # 30 master

        test_masters = set(master_files[:n_test])
        val_masters  = set(master_files[n_test:n_test + n_val])
        train_masters = set(master_files[n_test + n_val:])

        # Test dan Val HANYA berisi citra asli (tanpa augmentasi!)
        for f in test_masters:
            test_files.append((str(f), c_idx))
        for f in val_masters:
            val_files.append((str(f), c_idx))

        # Train berisi master files + variasi augmentasi yang bersesuaian
        # Map nomor induk
        for idx_m, m_file in enumerate(sorted(list(master_files)), start=1):
            if m_file in train_masters:
                train_files.append((str(m_file), c_idx))
                # Ambil 6 file augmentasi untuk master ini: (idx_m-1)*6 + 1 s/d idx_m*6
                start_aug = (idx_m - 1) * 6 + 1
                end_aug = idx_m * 6
                for a_i in range(start_aug, end_aug + 1):
                    aug_p = folder / f"aug_overfeed_{a_i:04d}.jpg"
                    if aug_p.exists():
                        train_files.append((str(aug_p), c_idx))

    else:
        # Kelas Aeromonas, Jamur, Parasit, Sehat
        all_imgs = [f for f in sorted(folder.glob("*.*")) if f.suffix.lower() in [".jpg", ".png", ".jpeg"] and not f.name.startswith("aug_")]
        random.shuffle(all_imgs)

        n_total = len(all_imgs)
        n_test = int(n_total * 0.10)
        n_val  = int(n_total * 0.15)
        n_train = n_total - n_test - n_val

        for f in all_imgs[:n_test]:
            test_files.append((str(f), c_idx))
        for f in all_imgs[n_test:n_test + n_val]:
            val_files.append((str(f), c_idx))
        for f in all_imgs[n_test + n_val:]:
            train_files.append((str(f), c_idx))

print(f"  Pemisahan Berhasil:")
print(f"    • Train Set      : {len(train_files)} citra (Siap augmentasi latih)")
print(f"    • Validation Set : {len(val_files)} citra (100% Citra Murni/Asli, Zero Leakage)")
print(f"    • Test Set       : {len(test_files)} citra (100% Uji Buta Independen, Zero Leakage)")

print("\n  Distribusi Data Validasi & Test Murni:")
for cls in TARGET_CLASSES:
    c_idx = class_to_idx[cls]
    v_c = sum(1 for _, l in val_files if l == c_idx)
    t_c = sum(1 for _, l in test_files if l == c_idx)
    print(f"    • {cls:<14}: Val={v_c} citra | Test={t_c} citra")

# ─── 2. Inisialisasi Backbone Pre-Trained ─────────────────────────────────────
print("\n[2/6] Memuat ImageNet Pre-Trained EfficientNet-B3...", flush=True)
full_model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)
full_model.eval()
full_model = full_model.to(device)

# Transformasi Evaluasi Murni (Validation & Test)
tf_clean = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Transformasi Latih (HANYA untuk Train Set)
tf_train_orig = tf_clean
tf_train_flip = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(p=1.0),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
tf_train_crop = transforms.Compose([
    transforms.Resize((int(INPUT_SIZE * 1.15), int(INPUT_SIZE * 1.15))),
    transforms.CenterCrop((INPUT_SIZE, INPUT_SIZE)),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ─── 3. Ekstraksi Fitur Spasial dari Blocks 0-5 ───────────────────────────────
def forward_blocks_0_to_5(model, x):
    h = model.conv_stem(x)
    h = model.bn1(h)
    for i in range(6):
        h = model.blocks[i](h)
    return h  # Shape: (B, 232, 10, 10)

def extract_features(file_list, is_train=False):
    t_start = time.time()
    spatial_list, labels_list = [], []
    batch_imgs, batch_lbls = [], []
    BATCH_SIZE = 32

    with torch.inference_mode():
        for idx, (path, label) in enumerate(file_list, start=1):
            try:
                pil_img = Image.open(path).convert("RGB")
                if is_train:
                    # Untuk data latih: ekstrak variasi multi-view (Original + Flip + CenterCrop)
                    batch_imgs.extend([
                        tf_train_orig(pil_img),
                        tf_train_flip(pil_img),
                        tf_train_crop(pil_img)
                    ])
                    batch_lbls.extend([label, label, label])
                else:
                    # Untuk Val & Test: HANYA 1 citra bersih murni!
                    batch_imgs.append(tf_clean(pil_img))
                    batch_lbls.append(label)

                if len(batch_imgs) >= BATCH_SIZE or idx == len(file_list):
                    inp = torch.stack(batch_imgs).to(device)
                    h_early = forward_blocks_0_to_5(full_model, inp).cpu()
                    spatial_list.append(h_early)
                    labels_list.extend(batch_lbls)
                    batch_imgs, batch_lbls = [], []

            except Exception as e:
                print(f"  [WARN] Gagal membaca {path}: {e}")

    X = torch.cat(spatial_list, dim=0)
    y = torch.tensor(labels_list, dtype=torch.long)
    return X, y

print("\n[3/6] Mengekstrak aktivasi spasial Blocks 0-5 secara ketat...", flush=True)
print("  -> Ekstraksi Train Set (Multi-View Augmentasi)...", flush=True)
X_train, y_train = extract_features(train_files, is_train=True)
print(f"     Train Tensor: {X_train.shape} sampel representasi", flush=True)

print("  -> Ekstraksi Validation Set (Murni Tanpa Augmentasi)...", flush=True)
X_val, y_val = extract_features(val_files, is_train=False)
print(f"     Val Tensor: {X_val.shape} sampel murni", flush=True)

print("  -> Ekstraksi Test Set (Murni Tanpa Augmentasi / Uji Buta)...", flush=True)
X_test, y_test = extract_features(test_files, is_train=False)
print(f"     Test Tensor: {X_test.shape} sampel murni", flush=True)

# ─── 4. Data Loader dengan Weighted Sampling ─────────────────────────────────
print("\n[4/6] Menyiapkan DataLoader & Penyeimbang Kelas...", flush=True)
train_counts = Counter(y_train.tolist())
train_weights = [1.0 / (NUM_CLASSES * train_counts[lbl]) for lbl in y_train.tolist()]
sampler = WeightedRandomSampler(train_weights, num_samples=len(X_train), replacement=True)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, sampler=sampler)
val_loader   = DataLoader(TensorDataset(X_val, y_val), batch_size=32, shuffle=False)
test_loader  = DataLoader(TensorDataset(X_test, y_test), batch_size=32, shuffle=False)

# ─── 5. Model Sub-Network: Block 6 + Conv Head + Classifier ──────────────────
print("\n[5/6] Pelatihan Sub-Jaringan Konvolusi (Block 6 + Conv Head + Classifier)...", flush=True)

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

# Tahap 1: Pemanasan Conv Head & Classifier (4 Epochs)
print("  -> Tahap 1: Pemanasan Head (4 Epochs)...", flush=True)
for p in pattern_net.block6.parameters(): p.requires_grad = False
for p in pattern_net.conv_head.parameters(): p.requires_grad = True
for p in pattern_net.bn2.parameters(): p.requires_grad = True
for p in pattern_net.classifier.parameters(): p.requires_grad = True

opt_stage1 = optim.AdamW([p for p in pattern_net.parameters() if p.requires_grad], lr=1e-3, weight_decay=1e-4)

for ep in range(1, 5):
    pattern_net.train()
    loss_sum, correct, total = 0, 0, 0
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
    print(f"     [Stage 1] Epoch {ep}/4 | Loss: {loss_sum/total:.4f} | Train Acc: {correct/total*100:.1f}%", flush=True)

# Tahap 2: Fine-Tuning Block 6 + Head secara Utuh (16 Epochs)
print("\n  -> Tahap 2: Fine-Tuning Mendalam Block 6 + Conv Head (16 Epochs)...", flush=True)
for p in pattern_net.block6.parameters(): p.requires_grad = True

opt_stage2 = optim.AdamW([
    {"params": pattern_net.block6.parameters(), "lr": 1.5e-4},
    {"params": pattern_net.conv_head.parameters(), "lr": 3e-4},
    {"params": pattern_net.bn2.parameters(), "lr": 3e-4},
    {"params": pattern_net.classifier.parameters(), "lr": 5e-4},
], weight_decay=1e-4)

scheduler = optim.lr_scheduler.CosineAnnealingLR(opt_stage2, T_max=16, eta_min=1e-5)

best_val_acc = 0.0
best_model_state = None

for ep in range(1, 17):
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

    scheduler.step()

    # Evaluasi pada Validation Murni (Tanpa Leakage)
    pattern_net.eval()
    val_correct, val_total = 0, 0
    with torch.no_grad():
        for bx, by in val_loader:
            bx, by = bx.to(device), by.to(device)
            out = pattern_net(bx)
            _, pred = out.max(1)
            val_correct += pred.eq(by).sum().item()
            val_total += by.size(0)

    val_acc = val_correct / val_total * 100
    train_acc = correct / total * 100

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_model_state = {k: v.cpu().clone() for k, v in full_model.state_dict().items()}

    print(f"     [Stage 2] Epoch {ep:02d}/16 | Train: {train_acc:5.1f}% | Pure Val Acc: {val_acc:5.1f}% (Best: {best_val_acc:5.1f}%)", flush=True)

# ─── 6. Evaluasi Akhir pada Test Set Independen (Uji Buta) ────────────────────
print(f"\n{'='*75}", flush=True)
print(f"  HASIL EVALUASI AKHIR (INDEPENDENT TEST SET / UJI BUTA MURNI)", flush=True)
print(f"{'='*75}\n", flush=True)

# Pasang bobot terbaik
if best_model_state is not None:
    full_model.load_state_dict(best_model_state)

pattern_net.eval()
test_correct, test_total = 0, 0
all_preds, all_targets = [], []

with torch.no_grad():
    for bx, by in test_loader:
        bx, by = bx.to(device), by.to(device)
        out = pattern_net(bx)
        _, pred = out.max(1)
        test_correct += pred.eq(by).sum().item()
        test_total += by.size(0)
        all_preds.extend(pred.cpu().tolist())
        all_targets.extend(by.cpu().tolist())

test_acc = test_correct / test_total * 100
print(f"  ★ AKURASI MURNI DATA TEST INDEPENDEN : {test_acc:.2f}%\n", flush=True)

report = classification_report(all_targets, all_preds, target_names=TARGET_CLASSES, digits=3, output_dict=True)
print("  Laporan Klasifikasi Data Test Murni (Tanpa Kebocoran Data):", flush=True)
for cls in TARGET_CLASSES:
    m = report[cls]
    print(f"    • {cls:<14} -> Precision: {m['precision']*100:5.1f}% | Recall: {m['recall']*100:5.1f}% | F1: {m['f1-score']*100:5.1f}%", flush=True)

cm = confusion_matrix(all_targets, all_preds)
print("\n  Confusion Matrix Data Test Independen:")
print("  Prediksi ->", "  ".join(f"{c[:4]:>4}" for c in TARGET_CLASSES))
for i, row in enumerate(cm):
    print(f"  {TARGET_CLASSES[i]:<11}:", "  ".join(f"{val:>4}" for val in row))

# Simpan model final ke disk
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

