"""
Training script EfficientNet-B3 untuk klasifikasi penyakit lele.

Dataset sumber: Kaggle - Freshwater Fish Disease Aquaculture In South Asia
URL: https://www.kaggle.com/datasets/subirbiswas19/freshwater-fish-disease-aquaculture-in-south-asia
Kelas asli (7): Aeromoniasis, Bacterial_Gill_Disease, Bacterial_Red_Disease,
               Saprolegniasis, Healthy, Parasitic_Disease, Viral_White_Tail_Disease

Mapping ke label Ternak Lele (5):
  Aeromoniasis           → Aeromonas
  Bacterial_Red_Disease  → Bercak_Merah
  Bacterial_Gill_Disease → Bercak_Merah  (digabung karena gejala visual mirip)
  Saprolegniasis         → Jamur
  Parasitic_Disease      → Parasit
  Viral_White_Tail_Disease → Parasit     (digabung, gejala visual mirip parasit)
  Healthy                → Sehat

Cara jalankan:
  python core/ai/train.py --data_dir ./dataset/fish_disease --epochs 30 --output ./core/ai/models/efficientnet_lele.pth
"""

import argparse
import os
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import transforms, datasets
import timm

# ------------------------------------------------------------------ #
#  Mapping kelas dataset sumber → label Ternak Lele
# ------------------------------------------------------------------ #
LABEL_MAP = {
    # Kaggle dataset class name (case-insensitive substring match)
    "aeromoniasis":          "Aeromonas",
    "bacterial_red_disease": "Bercak_Merah",
    "bacterial_gill":        "Bercak_Merah",
    "saprolegniasis":        "Jamur",
    "fungal":                "Jamur",
    "parasitic":             "Parasit",
    "viral":                 "Parasit",
    "healthy":               "Sehat",
}

TARGET_CLASSES = ["Sehat", "Aeromonas", "Bercak_Merah", "Jamur", "Parasit"]
NUM_CLASSES = len(TARGET_CLASSES)
INPUT_SIZE = 300


def remap_label(folder_name: str) -> str | None:
    """Petakan nama folder dataset ke label target Ternak Lele.
    Support: nama langsung (Sehat, Aeromonas, dll) atau nama Kaggle (aeromoniasis, dll).
    """
    # Cek dulu apakah nama folder sudah cocok persis dengan TARGET_CLASSES
    if folder_name in TARGET_CLASSES:
        return folder_name

    # Fallback: substring match ke LABEL_MAP (untuk dataset Kaggle)
    name_lower = folder_name.lower().replace(" ", "_")
    for key, target in LABEL_MAP.items():
        if key in name_lower:
            return target
    return None


# ------------------------------------------------------------------ #
#  Dataset dengan remapping otomatis
# ------------------------------------------------------------------ #
class RemappedDataset(torch.utils.data.Dataset):
    """
    Dataset wrapper yang remap label dari kelas sumber ke TARGET_CLASSES.
    Menangani folder yang tidak dikenali secara otomatis.
    """

    def __init__(self, root: str, transform=None):
        self.samples = []
        self.transform = transform
        self.class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}

        root_path = Path(root)
        skipped = []

        for folder in sorted(root_path.iterdir()):
            if not folder.is_dir():
                continue
            target_label = remap_label(folder.name)
            if target_label is None:
                skipped.append(folder.name)
                continue
            label_idx = self.class_to_idx[target_label]
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                for img_path in folder.glob(ext):
                    self.samples.append((str(img_path), label_idx))

        if skipped:
            print(f"[WARN] Folder tidak dikenali dan dilewati: {skipped}")
        print(f"[INFO] Total sampel: {len(self.samples)} dari {root}")

        # Hitung distribusi kelas
        from collections import Counter
        dist = Counter(label for _, label in self.samples)
        for idx, name in enumerate(TARGET_CLASSES):
            print(f"  {name}: {dist.get(idx, 0)} gambar")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        from PIL import Image
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label

    def get_class_weights(self) -> torch.Tensor:
        """Hitung bobot per kelas untuk WeightedRandomSampler (handle imbalance)."""
        from collections import Counter
        counts = Counter(label for _, label in self.samples)
        total = len(self.samples)
        weights = []
        for _, label in self.samples:
            weights.append(total / (NUM_CLASSES * counts[label]))
        return torch.tensor(weights, dtype=torch.float)


# ------------------------------------------------------------------ #
#  Data augmentation & transforms
# ------------------------------------------------------------------ #
def get_transforms(phase: str):
    if phase == "train":
        return transforms.Compose([
            transforms.RandomResizedCrop(INPUT_SIZE, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
            transforms.RandomRotation(20),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    else:
        return transforms.Compose([
            transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])


# ------------------------------------------------------------------ #
#  Training loop
# ------------------------------------------------------------------ #
def train_model(data_dir: str, output_path: str, epochs: int = 30,
                batch_size: int = 32, lr: float = 1e-4, val_split: float = 0.2):

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[INFO] Device: {device}")
    print(f"[INFO] Training EfficientNet-B3 — {NUM_CLASSES} kelas\n")

    # --- Dataset ---
    full_dataset = RemappedDataset(data_dir, transform=get_transforms("train"))
    val_size = int(len(full_dataset) * val_split)
    train_size = len(full_dataset) - val_size
    train_dataset, val_dataset = torch.utils.data.random_split(full_dataset, [train_size, val_size])

    # Override transform untuk val
    val_dataset.dataset = RemappedDataset(data_dir, transform=get_transforms("val"))

    # WeightedRandomSampler untuk handle class imbalance
    sample_weights = full_dataset.get_class_weights()
    train_weights = sample_weights[train_dataset.indices]
    sampler = WeightedRandomSampler(train_weights, len(train_weights), replacement=True)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, sampler=sampler,
                              num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False,
                            num_workers=4, pin_memory=True)

    print(f"[INFO] Train: {train_size} | Val: {val_size}")

    # --- Model: EfficientNet-B3 dengan ImageNet pretrained ---
    model = timm.create_model("efficientnet_b3", pretrained=True, num_classes=NUM_CLASSES)
    model.to(device)

    # Freeze backbone awal, hanya latih classifier head dulu (5 epoch pertama)
    for param in model.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()),
                            lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        # Unfreeze seluruh model setelah epoch ke-5
        if epoch == 6:
            print("[INFO] Unfreeze seluruh model untuk fine-tuning...")
            for param in model.parameters():
                param.requires_grad = True
            optimizer = optim.AdamW(model.parameters(), lr=lr * 0.1, weight_decay=1e-4)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs - 5)

        # --- Train phase ---
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0
        t0 = time.time()

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            train_correct += predicted.eq(labels).sum().item()
            train_total += labels.size(0)

        # --- Val phase ---
        model.eval()
        val_loss, val_correct, val_total = 0.0, 0, 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)

        scheduler.step()

        train_acc = train_correct / train_total * 100
        val_acc = val_correct / val_total * 100
        elapsed = time.time() - t0

        print(
            f"Epoch [{epoch:02d}/{epochs}] "
            f"Train Loss: {train_loss/train_total:.4f} Acc: {train_acc:.1f}% | "
            f"Val Loss: {val_loss/val_total:.4f} Acc: {val_acc:.1f}% | "
            f"Time: {elapsed:.1f}s"
        )

        # Simpan model terbaik
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), output_path)
            print(f"  ✓ Best model disimpan → {output_path} (Val Acc: {val_acc:.1f}%)")

    print(f"\n[DONE] Training selesai. Best Val Accuracy: {best_val_acc:.1f}%")
    print(f"       Model disimpan di: {output_path}")
    return best_val_acc


# ------------------------------------------------------------------ #
#  Evaluasi & Classification Report
# ------------------------------------------------------------------ #
def evaluate_model(model_path: str, data_dir: str, batch_size: int = 32):
    """Evaluasi model dengan classification report per kelas."""
    import numpy as np
    from sklearn.metrics import classification_report, confusion_matrix

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=NUM_CLASSES)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    dataset = RemappedDataset(data_dir, transform=get_transforms("val"))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    all_preds, all_labels = [], []
    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())

    print("\n=== Classification Report ===")
    print(classification_report(all_labels, all_preds, target_names=TARGET_CLASSES))
    print("=== Confusion Matrix ===")
    print(confusion_matrix(all_labels, all_preds))


# ------------------------------------------------------------------ #
#  Entry point
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Training EfficientNet-B3 Ternak Lele")
    parser.add_argument("--data_dir", type=str, required=True,
                        help="Path ke folder dataset (berisi subfolder per kelas)")
    parser.add_argument("--output", type=str,
                        default="core/ai/models/efficientnet_lele.pth",
                        help="Path output file model .pth")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--evaluate", action="store_true",
                        help="Jalankan evaluasi setelah training")

    args = parser.parse_args()

    best_acc = train_model(
        data_dir=args.data_dir,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )

    if args.evaluate:
        evaluate_model(args.output, args.data_dir, args.batch_size)
