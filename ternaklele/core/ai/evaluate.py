"""
Script evaluasi model terlatih.

Cara jalankan:
  python core/ai/evaluate.py --model core/ai/models/efficientnet_lele.pth --data_dir ./dataset/fish_disease
  python core/ai/evaluate.py --model core/ai/models/efficientnet_lele.pth --image path/to/lele.jpg
"""

import argparse
from pathlib import Path

import torch
import torch.nn.functional as F
import timm

TARGET_CLASSES = ["Sehat", "Aeromonas", "Bercak_Merah", "Jamur", "Parasit"]
INPUT_SIZE = 300


def load_model(model_path: str, device: torch.device):
    model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=len(TARGET_CLASSES))
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model


def predict_single(model_path: str, image_path: str):
    """Prediksi satu gambar dan tampilkan hasil."""
    import cv2
    import numpy as np

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(model_path, device)

    # Preprocessing
    img = cv2.imread(image_path)
    if img is None:
        print(f"ERROR: Gambar tidak dapat dibaca: {image_path}")
        return

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (INPUT_SIZE, INPUT_SIZE))
    img = img.astype("float32") / 255.0
    img = (img - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    tensor = torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1).squeeze()

    print(f"\n=== Hasil Prediksi: {image_path} ===")
    for i, (label, prob) in enumerate(zip(TARGET_CLASSES, probs)):
        marker = "◀ PREDIKSI" if i == probs.argmax().item() else ""
        print(f"  {label:20s}: {prob * 100:6.2f}% {marker}")


def full_evaluation(model_path: str, data_dir: str, batch_size: int = 32):
    """Evaluasi lengkap dengan confusion matrix dan classification report."""
    from sklearn.metrics import classification_report, confusion_matrix
    from torchvision import transforms
    from torch.utils.data import DataLoader
    import numpy as np
    import sys
    import os

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core.ai.train import RemappedDataset, get_transforms

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(model_path, device)

    dataset = RemappedDataset(data_dir, transform=get_transforms("val"))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    all_preds, all_labels = [], []
    correct = 0
    total = 0

    print("Mengevaluasi model...")
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            predicted = predicted.cpu()
            all_preds.extend(predicted.numpy())
            all_labels.extend(labels.numpy())
            correct += predicted.eq(labels).sum().item()
            total += labels.size(0)

    accuracy = correct / total * 100
    print(f"\nOverall Accuracy: {accuracy:.2f}%")
    print("\n=== Classification Report ===")
    print(classification_report(all_labels, all_preds, target_names=TARGET_CLASSES, digits=4))

    cm = confusion_matrix(all_labels, all_preds)
    print("=== Confusion Matrix ===")
    print(f"{'':15s}", end="")
    for c in TARGET_CLASSES:
        print(f"{c[:10]:>12s}", end="")
    print()
    for i, row in enumerate(cm):
        print(f"{TARGET_CLASSES[i]:15s}", end="")
        for val in row:
            print(f"{val:12d}", end="")
        print()

    # Hitung precision per kelas (target ≥ 0.88 per SRS)
    from sklearn.metrics import precision_score
    precisions = precision_score(all_labels, all_preds, average=None)
    print("\n=== Precision per Kelas (Target ≥ 88%) ===")
    for label, prec in zip(TARGET_CLASSES, precisions):
        status = "✓" if prec >= 0.88 else "✗"
        print(f"  {status} {label:20s}: {prec * 100:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluasi model Ternak Lele")
    parser.add_argument("--model", type=str, required=True, help="Path ke file .pth")
    parser.add_argument("--data_dir", type=str, default=None,
                        help="Path dataset untuk evaluasi penuh")
    parser.add_argument("--image", type=str, default=None,
                        help="Path satu gambar untuk prediksi cepat")
    parser.add_argument("--batch_size", type=int, default=32)

    args = parser.parse_args()

    if args.image:
        predict_single(args.model, args.image)
    elif args.data_dir:
        full_evaluation(args.model, args.data_dir, args.batch_size)
    else:
        print("Gunakan --image untuk prediksi satu gambar, atau --data_dir untuk evaluasi penuh.")
