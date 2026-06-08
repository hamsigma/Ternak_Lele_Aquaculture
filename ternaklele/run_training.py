"""
Script training mandiri — tidak perlu pretrained weights download.
Langsung train dari scratch dengan augmentasi kuat.
"""
import sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler, random_split
from torchvision import transforms
from PIL import Image
from pathlib import Path
from collections import Counter

# ── Konfigurasi ─────────────────────────────────────────
DATA_DIR    = "./dataset/fish_disease"
OUTPUT_PATH = "./core/ai/models/efficientnet_lele.pth"
EPOCHS      = 25
BATCH_SIZE  = 32
LR          = 3e-4
VAL_SPLIT   = 0.2
IMG_SIZE    = 224
TARGET_CLASSES = ["Sehat", "Aeromonas", "Bercak_Merah", "Jamur", "Parasit"]
NUM_CLASSES = len(TARGET_CLASSES)

# ── Dataset ──────────────────────────────────────────────
class FishDataset(torch.utils.data.Dataset):
    def __init__(self, root, transform=None):
        self.transform = transform
        self.class_to_idx = {c: i for i, c in enumerate(TARGET_CLASSES)}
        self.samples = []
        for folder in Path(root).iterdir():
            if folder.is_dir() and folder.name in TARGET_CLASSES:
                idx = self.class_to_idx[folder.name]
                for img_path in folder.glob("*.jpg"):
                    self.samples.append((str(img_path), idx))
        print(f"  Loaded {len(self.samples)} samples")
        dist = Counter(lbl for _, lbl in self.samples)
        for i, name in enumerate(TARGET_CLASSES):
            print(f"    {name}: {dist.get(i,0)}")

    def __len__(self): return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform: img = self.transform(img)
        return img, label

    def get_weights(self):
        counts = Counter(lbl for _, lbl in self.samples)
        total = len(self.samples)
        return torch.tensor([total / (NUM_CLASSES * counts[lbl]) for _, lbl in self.samples])

# ── Transforms ───────────────────────────────────────────
train_tf = transforms.Compose([
    transforms.RandomResizedCrop(IMG_SIZE, scale=(0.7,1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])
val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

# ── Model: EfficientNet-B0 ringan tanpa pretrained ────────
import timm

def build_model():
    # Gunakan mobilenetv3 kecil — cepat, tidak butuh download besar
    try:
        model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=NUM_CLASSES)
        print("  Model: EfficientNet-B0 (from scratch)")
    except Exception:
        # Ultra fallback: simple CNN
        model = SimpleCNN(NUM_CLASSES)
        print("  Model: SimpleCNN fallback")
    return model

class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3,32,3,padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32,64,3,padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64,128,3,padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(128,256,3,padding=1), nn.BatchNorm2d(256), nn.ReLU(), nn.AdaptiveAvgPool2d(4),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(0.4),
            nn.Linear(256*4*4, 512), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    def forward(self, x): return self.classifier(self.features(x))

# ── Main ─────────────────────────────────────────────────
def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*50}")
    print(f" Ternak Lele AI Training")
    print(f"{'='*50}")
    print(f"  Device: {device}")
    print(f"  Epochs: {EPOCHS}, Batch: {BATCH_SIZE}, LR: {LR}")
    print(f"\nLoading dataset...")

    full = FishDataset(DATA_DIR, train_tf)
    val_size = int(len(full) * VAL_SPLIT)
    train_size = len(full) - val_size
    train_ds, val_ds = random_split(full, [train_size, val_size],
                                    generator=torch.Generator().manual_seed(42))

    # Val dataset pakai val_tf
    val_full = FishDataset(DATA_DIR, val_tf)
    val_ds = torch.utils.data.Subset(val_full, val_ds.indices)

    # Weighted sampler
    weights = full.get_weights()
    train_weights = weights[[i for i in train_ds.indices]]
    sampler = WeightedRandomSampler(train_weights, len(train_weights))

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, sampler=sampler, num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,  num_workers=0)
    print(f"  Train: {train_size} | Val: {val_size}")

    print("\nBuilding model...")
    model = build_model().to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    best_val_acc = 0.0

    print(f"\nStarting training...\n")
    for epoch in range(1, EPOCHS+1):
        # Train
        model.train()
        t_loss = t_correct = t_total = 0
        t0 = time.time()
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(inputs), labels)
            loss.backward()
            optimizer.step()
            t_loss   += loss.item() * inputs.size(0)
            t_correct+= (model(inputs).argmax(1) == labels).sum().item()
            t_total  += labels.size(0)

        # Val
        model.eval()
        v_loss = v_correct = v_total = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                out = model(inputs)
                v_loss   += criterion(out, labels).item() * inputs.size(0)
                v_correct+= (out.argmax(1) == labels).sum().item()
                v_total  += labels.size(0)

        scheduler.step()
        t_acc = t_correct/t_total*100
        v_acc = v_correct/v_total*100
        elapsed = time.time()-t0

        print(f"Epoch [{epoch:02d}/{EPOCHS}] "
              f"Train {t_loss/t_total:.4f}/{t_acc:.1f}% | "
              f"Val {v_loss/v_total:.4f}/{v_acc:.1f}% | "
              f"{elapsed:.0f}s", end="")

        if v_acc > best_val_acc:
            best_val_acc = v_acc
            torch.save(model.state_dict(), OUTPUT_PATH)
            print(f" ✓ BEST saved", end="")
        print()

    print(f"\n{'='*50}")
    print(f" Training selesai! Best Val Acc: {best_val_acc:.1f}%")
    print(f" Model: {OUTPUT_PATH}")
    print(f"{'='*50}\n")
    return best_val_acc

if __name__ == "__main__":
    main()
