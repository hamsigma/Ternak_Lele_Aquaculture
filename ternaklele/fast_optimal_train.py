"""
fast_optimal_train.py — Training Cepat & Akurat Menggunakan Pre-Trained Features
================================================================================
1. Menggunakan ImageNet pre-trained EfficientNet-B3 untuk ekstraksi feature vector 1536-D.
2. Augmentasi data (original + horizontal flip) menghasilkan ~2.880 sampel representasi.
3. Ekstraksi fitur dalam mode inferensi 8 CPU threads (sangat cepat, ~1-2 menit).
4. Pelatihan classifier head 80 epoch dengan WeightedRandomSampler & Label Smoothing 0.08 (~2 detik).
5. Validasi komprehensif (Precision, Recall, F1) dan pengujian khusus pada gambar lele riil.
6. Menyimpan model akhir lengkap ke core/ai/models/efficientnet_lele.pth.
"""

import os, sys, time, random
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
LABEL_SMOOTHING = 0.08

print(f"{'='*70}", flush=True)
print(f"  TERNAK LELE AI — FAST & OPTIMAL EFFICIENTNET-B3 TRAINING", flush=True)
print(f"  Device          : {device} (8 CPU Threads)", flush=True)
print(f"  Target Classes  : {TARGET_CLASSES}", flush=True)
print(f"  Model Output    : {OUTPUT_PATH}", flush=True)
print(f"{'='*70}\n", flush=True)

# ─── 1. Kumpulkan Semua Sampel ───────────────────────────────────────────────
print("[1/5] Memindai file gambar dataset...", flush=True)
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
print(f"  Total Gambar: {len(all_samples)}")
for i, name in enumerate(TARGET_CLASSES):
    print(f"    • {name:<14}: {counts.get(i, 0)} gambar")

# ─── 2. Ekstraksi Fitur 1536-D Menggunakan Backbone ImageNet Pretrained ───────
print("\n[2/5] Memuat ImageNet Pre-trained Backbone...", flush=True)
backbone = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)
backbone.eval()
backbone = backbone.to(device)

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

print("\n[3/5] Mengekstrak embedding fitur 1536-D (Original + Augmented)...", flush=True)
t_start = time.time()

features_list = []
labels_list = []
meta_list = []

batch_imgs = []
batch_lbls = []
batch_meta = []
BATCH_EXTRACT = 32

with torch.inference_mode():
    for idx, (path, label, fname) in enumerate(all_samples, start=1):
        try:
            pil_img = Image.open(path).convert("RGB")
            t_orig = tf_orig(pil_img)
            t_flip = tf_flip(pil_img)

            batch_imgs.extend([t_orig, t_flip])
            batch_lbls.extend([label, label])
            batch_meta.extend([(fname, False), (fname, True)])

            if len(batch_imgs) >= BATCH_EXTRACT or idx == len(all_samples):
                inp = torch.stack(batch_imgs).to(device)
                feat = backbone.forward_features(inp)
                emb = backbone.forward_head(feat, pre_logits=True).cpu()
                features_list.append(emb)
                labels_list.extend(batch_lbls)
                meta_list.extend(batch_meta)

                batch_imgs = []
                batch_lbls = []
                batch_meta = []

            if idx % 200 == 0 or idx == len(all_samples):
                print(f"  Ekstraksi: {idx}/{len(all_samples)} gambar selesai ({time.time()-t_start:.1f}s)", flush=True)

        except Exception as e:
            print(f"  [WARN] Gagal proses {path}: {e}")

X = torch.cat(features_list, dim=0)
y = torch.tensor(labels_list, dtype=torch.long)
print(f"  Ekstraksi selesai! Shape Tensor Fitur: {X.shape} (dalam {time.time()-t_start:.1f}s)\n", flush=True)

# ─── 3. Train / Validation Split ─────────────────────────────────────────────
print("[4/5] Membagi Data Train (80%) dan Validasi (20%)...", flush=True)
N = len(X)
random.seed(42)
indices = list(range(N))
random.shuffle(indices)

n_val = int(N * 0.2)
val_indices = indices[:n_val]
train_indices = indices[n_val:]

X_train, y_train = X[train_indices], y[train_indices]
X_val, y_val     = X[val_indices], y[val_indices]

# WeightedRandomSampler untuk menyeimbangkan kelas pada training split
train_counts = Counter(y_train.tolist())
train_weights = [1.0 / (NUM_CLASSES * train_counts[lbl]) for lbl in y_train.tolist()]
sampler = WeightedRandomSampler(train_weights, num_samples=len(X_train), replacement=True)

train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=32, sampler=sampler)
val_loader   = DataLoader(TensorDataset(X_val, y_val), batch_size=64, shuffle=False)

print(f"  Train: {len(X_train)} sampel | Val: {len(X_val)} sampel\n", flush=True)

# ─── 4. Pelatihan Classifier Head ────────────────────────────────────────────
print("[5/5] Melatih Classifier Head (80 Epochs)...", flush=True)
classifier = nn.Linear(1536, NUM_CLASSES).to(device)
criterion = nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING)
optimizer = optim.AdamW(classifier.parameters(), lr=5e-3, weight_decay=1e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=80, eta_min=1e-5)

best_val_acc = 0.0
best_weights = None
best_report = None

for epoch in range(1, 81):
    classifier.train()
    train_correct = 0
    train_total = 0
    for bx, by in train_loader:
        bx, by = bx.to(device), by.to(device)
        optimizer.zero_grad()
        out = classifier(bx)
        loss = criterion(out, by)
        loss.backward()
        optimizer.step()

        _, pred = out.max(1)
        train_correct += pred.eq(by).sum().item()
        train_total += by.size(0)

    scheduler.step()

    # Evaluasi Val
    classifier.eval()
    val_correct = 0
    val_total = 0
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for bx, by in val_loader:
            bx, by = bx.to(device), by.to(device)
            out = classifier(bx)
            _, pred = out.max(1)
            val_correct += pred.eq(by).sum().item()
            val_total += by.size(0)
            all_preds.extend(pred.cpu().tolist())
            all_targets.extend(by.cpu().tolist())

    val_acc = val_correct / val_total * 100
    train_acc = train_correct / train_total * 100

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        best_weights = {k: v.cpu().clone() for k, v in classifier.state_dict().items()}
        best_report = classification_report(all_targets, all_preds, target_names=TARGET_CLASSES, digits=3, output_dict=True)

    if epoch % 10 == 0 or epoch == 80:
        print(f"  Epoch {epoch:02d}/80 | Train Acc: {train_acc:5.1f}% | Val Acc: {val_acc:5.1f}% (Best: {best_val_acc:5.1f}%)", flush=True)

# ─── 5. Simpan Model Lengkap EfficientNet-B3 ─────────────────────────────────
print(f"\n{'='*70}", flush=True)
print(f"  HASIL AKHIR PELATIHAN CLASSIFIER", flush=True)
print(f"  Best Validation Accuracy: {best_val_acc:.2f}%", flush=True)
print(f"{'='*70}\n", flush=True)

if best_report:
    print("  Laporan Evaluasi per Kelas:", flush=True)
    for cls in TARGET_CLASSES:
        m = best_report[cls]
        print(f"    • {cls:<14} -> Precision: {m['precision']*100:5.1f}% | Recall: {m['recall']*100:5.1f}% | F1: {m['f1-score']*100:5.1f}%", flush=True)

# Pasang bobot terbaik ke backbone resmi
backbone.classifier.load_state_dict(best_weights)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
torch.save(backbone.state_dict(), OUTPUT_PATH)
print(f"\n[INFO] Model final lengkap berhasil disimpan ke: {OUTPUT_PATH}", flush=True)

# ─── 6. Verifikasi Khusus pada Sampel Gambar Lele Riil ────────────────────────
print("\n[VERIFIKASI] Menguji model pada sampel gambar lele riil:", flush=True)
backbone.eval()
test_real = [
    ("Aeromonas", "dataset/fish_disease/Aeromonas/real_aeromonas15.jpg"),
    ("Aeromonas", "dataset/fish_disease/Aeromonas/real_aeromonas_16.jpg"),
    ("Jamur",     "dataset/fish_disease/Jamur/real_jamur_04.jpg"),
    ("Jamur",     "dataset/fish_disease/Jamur/real_jamur_03.jpg"),
    ("Jamur",     "dataset/fish_disease/Jamur/real_jamur_lele.jpg"),
    ("Sehat",     "dataset/fish_disease/Sehat/real_lele_sehat_01.jpg"),
    ("Overfeeding", "dataset/fish_disease/Overfeeding/real_overfeeding_01.jpg"),
    ("Parasit",   "dataset/fish_disease/Parasit/real_parasit_01.jpg"),
]

for true_cls, p_str in test_real:
    p = ROOT / p_str
    if p.exists():
        im = tf_orig(Image.open(p).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            out = backbone(im)
            prob = torch.softmax(out, dim=1).squeeze()
            top_idx = int(prob.argmax().item())
            top_label = TARGET_CLASSES[top_idx]
            top_conf = float(prob[top_idx])
            mark = "OK  " if top_label == true_cls else "MISS"
            print(f"  {mark} [{true_cls:<11}] {p.name} -> {top_label} ({top_conf*100:.1f}%)", flush=True)

# Reset singleton classifier Django
try:
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    django.setup()
    import core.ai.classifier as clf_module
    clf_module._classifier_instance = None
    print("\n[INFO] Singleton classifier di-reset. Model aktif melayani inferensi di server.", flush=True)
except Exception as e:
    print(f"\n[INFO] Info reset Django: {e}", flush=True)

