"""
Train Head Only - Cepat (Head-only, 224px, batch 64)
Melatih hanya layer classifier akhir EfficientNet-B3.
Selesai dalam ~1-3 menit di CPU.
"""
import sys
import time
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
import timm

ROOT = Path("c:/Users/Administrator/Documents/Tenak Lele/ternaklele")
DATA_DIR = ROOT / "dataset" / "fish_disease"
OUTPUT_PATH = ROOT / "core" / "ai" / "models" / "efficientnet_lele.pth"

# Gunakan 224 untuk training cepat, model runtime tetap 300
INPUT_SIZE = 224
TARGET_CLASSES = ["Sehat", "Aeromonas", "Malnutrisi", "Jamur", "Overfeeding"]
NUM_CLASSES = len(TARGET_CLASSES)
EPOCHS = 3
BATCH_SIZE = 64


class FastDataset(Dataset):
    def __init__(self, root, transform=None):
        self.transform = transform
        self.samples = []
        for folder in sorted(Path(root).iterdir()):
            if not folder.is_dir():
                continue
            lbl = folder.name
            if lbl not in TARGET_CLASSES:
                continue
            idx = TARGET_CLASSES.index(lbl)
            for f in folder.glob("*"):
                if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                    self.samples.append((str(f), idx))
        print(f"[INFO] Loaded {len(self.samples)} sampel dari {len(TARGET_CLASSES)} kelas.")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


train_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize((INPUT_SIZE, INPUT_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

full_ds = FastDataset(DATA_DIR, transform=train_tf)
n_val = int(len(full_ds) * 0.15)
n_train = len(full_ds) - n_val
train_ds, val_ds = torch.utils.data.random_split(full_ds, [n_train, n_val])
val_ds.dataset = FastDataset(DATA_DIR, transform=val_tf)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
print(f"[INFO] Train: {n_train} | Val: {n_val}\n")

# ── Model ────────────────────────────────────────────────────────────────────
print("[INFO] Loading EfficientNet-B3...")
model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=NUM_CLASSES)

if OUTPUT_PATH.exists():
    state = torch.load(OUTPUT_PATH, map_location="cpu")
    model_state = model.state_dict()
    filtered = {k: v for k, v in state.items()
                if k in model_state and model_state[k].shape == v.shape}
    model.load_state_dict(filtered, strict=False)
    print(f"[INFO] Loaded {len(filtered)}/{len(model_state)} layers dari checkpoint.")

# FREEZE backbone, train ONLY classifier head
for param in model.parameters():
    param.requires_grad = False
# Unfreeze the head
for param in model.classifier.parameters():
    param.requires_grad = True

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total     = sum(p.numel() for p in model.parameters())
print(f"[INFO] Parameter trainable: {trainable:,} / {total:,} (hanya head)")

# ── Training ─────────────────────────────────────────────────────────────────
criterion = nn.CrossEntropyLoss()
optimizer = optim.AdamW(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=2e-3, weight_decay=1e-4
)

best_acc = 0.0
print(f"\nEpoch  Train Acc   Val Acc   Time")
print("-" * 40)

for epoch in range(1, EPOCHS + 1):
    t0 = time.time()
    model.train()
    tc = tt = 0
    for inputs, labels in train_loader:
        optimizer.zero_grad()
        out = model(inputs)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()
        _, pred = out.max(1)
        tc += pred.eq(labels).sum().item()
        tt += labels.size(0)

    model.eval()
    vc = vt = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            out = model(inputs)
            _, pred = out.max(1)
            vc += pred.eq(labels).sum().item()
            vt += labels.size(0)

    t_acc = tc / tt * 100
    v_acc = vc / vt * 100
    elapsed = time.time() - t0
    note = ""
    if v_acc >= best_acc:
        best_acc = v_acc
        torch.save(model.state_dict(), OUTPUT_PATH)
        note = "[SAVED]"

    print(f"  {epoch}/3   {t_acc:6.2f}%   {v_acc:6.2f}%   {elapsed:.1f}s  {note}")

print(f"\n[DONE] Training selesai! Best Val Acc: {best_acc:.2f}%")
print(f"[INFO] Model tersimpan di: {OUTPUT_PATH}")
print("[INFO] Hot-reload akan aktif otomatis pada request deteksi berikutnya.")
