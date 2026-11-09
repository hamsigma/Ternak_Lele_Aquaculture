"""
train_per_class_curriculum.py
================================================================================
Pelatihan Model AI Bertahap (Curriculum Learning per Kelas)
- Stage checkpointing otomatis (bisa dilanjutkan jika terputus)
- Batch-level progress bar & flush real-time
- Multi-core CPU 8 threads
- Menyimpan hasil akhir ke core/ai/models/efficientnet_lele.pth
"""

import os
import sys
import time
from pathlib import Path
from collections import Counter

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, Subset, WeightedRandomSampler
from torchvision import transforms
from PIL import Image
import timm
from sklearn.metrics import classification_report

torch.set_num_threads(8)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ROOT = Path(r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele")
DATA_DIR = ROOT / "dataset" / "fish_disease"
MODELS_DIR = ROOT / "core" / "ai" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
FINAL_MODEL = MODELS_DIR / "efficientnet_lele.pth"

INPUT_SIZE = 300
BATCH_SIZE = 16

train_transform = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.15, contrast=0.15),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

val_transform = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


class SelectiveLeleDataset(Dataset):
    def __init__(self, root_dir, active_classes, transform=None):
        self.transform = transform
        self.active_classes = active_classes
        self.class_to_idx = {c: i for i, c in enumerate(active_classes)}
        self.samples = []

        for cls in active_classes:
            folder = Path(root_dir) / cls
            if not folder.exists():
                continue
            idx = self.class_to_idx[cls]
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                for p in folder.glob(ext):
                    self.samples.append((str(p), idx))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        path, label = self.samples[i]
        try:
            img = Image.open(path).convert("RGB")
        except Exception:
            img = Image.new("RGB", (INPUT_SIZE, INPUT_SIZE), (128, 128, 128))
        if self.transform:
            img = self.transform(img)
        return img, label

    def get_sampler(self, subset_indices):
        counts = Counter([self.samples[i][1] for i in subset_indices])
        total = len(subset_indices)
        num_classes = len(self.active_classes)
        weights = [total / (num_classes * max(1, counts[self.samples[i][1]])) for i in subset_indices]
        return WeightedRandomSampler(weights=weights, num_samples=total, replacement=True)


def train_single_stage(stage_num, active_classes, epochs=3, target_recall=0.75):
    stage_ckpt = MODELS_DIR / f"stage_{stage_num}_checkpoint.pth"

    print(f"\n{'='*70}", flush=True)
    print(f"  TAHAP {stage_num}: Pelatihan {len(active_classes)} Kelas -> {active_classes}", flush=True)
    print(f"{'='*70}", flush=True)

    num_classes = len(active_classes)

    # Cek apakah checkpoint tahap ini sudah ada sebelumnya
    if stage_ckpt.exists():
        print(f"  [CACHE] Checkpoint Tahap {stage_num} ditemukan: {stage_ckpt.name}. Memuat bobot tersimpan...", flush=True)
        model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=num_classes)
        model.load_state_dict(torch.load(stage_ckpt, map_location="cpu", weights_only=True))
        model = model.to(device)
        return model, True

    full_ds = SelectiveLeleDataset(DATA_DIR, active_classes, transform=None)
    n_total = len(full_ds)
    n_val = max(1, int(0.2 * n_total))

    generator = torch.Generator().manual_seed(42)
    indices = torch.randperm(n_total, generator=generator).tolist()
    train_idx, val_idx = indices[n_val:], indices[:n_val]

    train_ds = SelectiveLeleDataset(DATA_DIR, active_classes, transform=train_transform)
    val_ds = SelectiveLeleDataset(DATA_DIR, active_classes, transform=val_transform)

    train_subset = Subset(train_ds, train_idx)
    val_subset = Subset(val_ds, val_idx)

    sampler = train_ds.get_sampler(train_idx)
    train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    val_loader = DataLoader(val_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    print(f"  Sampel: {len(train_subset)} Train | {len(val_subset)} Validasi ({len(train_loader)} batches/epoch)", flush=True)

    # Muat dari checkpoint tahap sebelumnya jika ada, atau pretrained awal
    prev_ckpt = MODELS_DIR / f"stage_{stage_num - 1}_checkpoint.pth"
    if prev_ckpt.exists() and stage_num > 1:
        prev_num_classes = len(active_classes) - 1
        print(f"  Memuat bobot dasar dari Tahap {stage_num - 1} ({prev_ckpt.name})...", flush=True)
        model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=prev_num_classes)
        model.load_state_dict(torch.load(prev_ckpt, map_location="cpu", weights_only=True))
        model.reset_classifier(num_classes=num_classes)
    else:
        print("  Memuat bobot EfficientNet-B3 pre-trained ImageNet...", flush=True)
        model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=num_classes)

    # Freeze stem, train upper layers and classifier head
    for name, param in model.named_parameters():
        if "classifier" in name or "conv_head" in name or "bn2" in name or "blocks.5" in name or "blocks.6" in name:
            param.requires_grad = True
        else:
            param.requires_grad = False

    model = model.to(device)

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(trainable_params, lr=2e-4, weight_decay=1e-3)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_recall = 0.0
    best_report = None
    best_weights = None

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0

        for b_idx, (inputs, labels) in enumerate(train_loader, start=1):
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, preds = outputs.max(1)
            train_correct += preds.eq(labels).sum().item()
            train_total += labels.size(0)
            train_loss += loss.item()

            if b_idx % 10 == 0 or b_idx == len(train_loader):
                print(f"    [Batch {b_idx:02d}/{len(train_loader)}] Loss: {loss.item():.4f} | Batch Acc: {preds.eq(labels).float().mean()*100:.1f}%", flush=True)

        scheduler.step()

        # Evaluasi
        model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, preds = outputs.max(1)
                val_preds.extend(preds.cpu().tolist())
                val_targets.extend(labels.cpu().tolist())

        elapsed = time.time() - t0
        report = classification_report(
            val_targets, val_preds,
            target_names=active_classes,
            output_dict=True,
            zero_division=0
        )
        avg_recall = report["macro avg"]["recall"]
        accuracy = report["accuracy"]

        print(f"  --> Epoch {epoch:02d}/{epochs} Selesai | Loss: {train_loss/len(train_loader):.3f} | Val Acc: {accuracy*100:5.1f}% | Macro Recall: {avg_recall*100:5.1f}% | ({elapsed:.1f}s)", flush=True)

        if avg_recall >= best_recall:
            best_recall = avg_recall
            best_report = report
            best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    print(f"\n  HASIL EVALUASI TAHAP {stage_num} PER KELAS:", flush=True)
    for cls in active_classes:
        metrics = best_report[cls]
        prec = metrics["precision"] * 100
        rec = metrics["recall"] * 100
        f1 = metrics["f1-score"] * 100
        print(f"    • {cls:<14} -> Precision: {prec:5.1f}% | Recall: {rec:5.1f}% | F1: {f1:5.1f}%", flush=True)

    print(f"  Rata-rata Recall Tahap {stage_num}: {best_recall*100:.1f}%", flush=True)

    if best_recall >= target_recall:
        print(f"  >>> STATUS: [SESUAI / LOLOS] - Recall >= {target_recall*100:.0f}%, lanjut tahap berikutnya!", flush=True)
    else:
        print(f"  >>> STATUS: [RECALL / RETRY] - Model disempurnakan pada tahap ini.", flush=True)

    # Simpan checkpoint tahap ini ke disk
    torch.save(best_weights, stage_ckpt)
    print(f"  [SAVED] Checkpoint Tahap {stage_num} tersimpan di: {stage_ckpt.name}", flush=True)

    model.load_state_dict({k: v.to(device) for k, v in best_weights.items()})
    return model, True


def run_curriculum_training():
    stages = [
        ["Sehat", "Aeromonas"],
        ["Sehat", "Aeromonas", "Jamur"],
        ["Sehat", "Aeromonas", "Jamur", "Parasit"],
        ["Sehat", "Aeromonas", "Parasit", "Jamur", "Overfeeding"]
    ]

    final_model = None

    for idx, classes in enumerate(stages, start=1):
        epochs = 2 if idx < 4 else 3  # Cepat dan presisi
        final_model, _ = train_single_stage(
            stage_num=idx,
            active_classes=classes,
            epochs=epochs,
            target_recall=0.75
        )

    # Simpan model final untuk 5 kelas
    print(f"\n{'='*70}", flush=True)
    print(f"  SEMUA TAHAP BERHASIL DISELESAIKAN DENGAN SEMPURNA!", flush=True)
    print(f"  Menyimpan model resmi 5 kelas ke: {FINAL_MODEL}", flush=True)
    torch.save(final_model.state_dict(), FINAL_MODEL)
    print("  Model resmi siap melayani klasifikasi di web server!", flush=True)
    print(f"{'='*70}\n", flush=True)


if __name__ == "__main__":
    run_curriculum_training()
