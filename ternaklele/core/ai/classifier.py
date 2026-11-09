"""
Modul klasifikasi penyakit lele menggunakan EfficientNet-B3.
Model dimuat sekali ke memori (singleton pattern) untuk efisiensi.
Preprocessing menggunakan OpenCV sebelum inferensi PyTorch.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_classifier_instance = None


class LeleClassifier:
    """
    Wrapper classifier EfficientNet-B3 untuk deteksi penyakit lele.
    Pipeline: OpenCV preprocessing → PyTorch EfficientNet-B3 → probabilitas kelas.
    """

    INPUT_SIZE = (300, 300)
    IMAGENET_MEAN = [0.485, 0.456, 0.406]
    IMAGENET_STD = [0.229, 0.224, 0.225]
    TEMPERATURE = 1.0  # Softmax standar terkalibrasi oleh label smoothing pada pelatihan

    def __init__(self):
        from django.conf import settings
        self.model_path: Path = settings.AI_MODEL_PATH
        self.class_labels: list = settings.AI_CLASS_LABELS
        self.model = None
        self.device = None
        self.last_loaded_time = 0
        self._load_model()

    def _load_model(self):
        """Load model EfficientNet-B3 dari file .pth ke GPU/CPU."""
        try:
            import torch
            import timm

            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Batasi thread PyTorch di CPU untuk mencegah CPU starvation pada Django server
            if self.device.type == "cpu":
                try:
                    if hasattr(torch, 'set_num_threads'):
                        torch.set_num_threads(1)
                    if hasattr(torch, 'set_interop_op_num_threads'):
                        torch.set_interop_op_num_threads(1)
                    logger.info("Optimasi CPU PyTorch aktif: membatasi thread menjadi 1 untuk kestabilan web server.")
                except Exception as thread_err:
                    logger.warning(f"Gagal mengatur opsi optimasi CPU thread: {thread_err}")

            num_classes = len(self.class_labels)

            self.model = timm.create_model(
                "efficientnet_b3",
                pretrained=False,
                num_classes=num_classes,
            )

            if self.model_path.exists():
                # Coba load dengan weights_only=True dulu (aman), fallback ke False
                try:
                    state_dict = torch.load(
                        self.model_path, map_location=self.device, weights_only=True
                    )
                except Exception:
                    state_dict = torch.load(
                        self.model_path, map_location=self.device, weights_only=False
                    )

                # Handle jika state_dict wrapped dalam key lain
                if isinstance(state_dict, dict) and "state_dict" in state_dict:
                    state_dict = state_dict["state_dict"]

                # Load dengan strict=False agar tahan perbedaan jumlah kelas
                model_state = self.model.state_dict()
                filtered = {
                    k: v for k, v in state_dict.items()
                    if k in model_state and model_state[k].shape == v.shape
                }
                missing, unexpected = self.model.load_state_dict(filtered, strict=False)
                self.last_loaded_time = self.model_path.stat().st_mtime
                logger.info(
                    f"Model dimuat dari {self.model_path} pada {self.device}. "
                    f"Loaded: {len(filtered)}/{len(model_state)} layers"
                )
            else:
                logger.warning(
                    f"File model tidak ditemukan di {self.model_path}. "
                    "Menggunakan bobot acak (mode testing)."
                )

            self.model.to(self.device)
            self.model.eval()

        except ImportError as e:
            logger.error(f"Library AI tidak tersedia: {e}")
            self.model = None
        except Exception as e:
            logger.error(f"Gagal memuat model: {e}")
            self.model = None

    def _preprocess_opencv(self, image_path: str):
        """
        Preprocessing gambar: OpenCV (utama) → PIL fallback.
        Pipeline: load → RGB → resize → normalize → tensor
        """
        import numpy as np
        import torch

        try:
            import cv2
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"OpenCV gagal baca: {image_path}")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, self.INPUT_SIZE, interpolation=cv2.INTER_AREA)
        except Exception:
            # Fallback ke PIL
            from PIL import Image
            img = Image.open(image_path).convert("RGB")
            img = img.resize(self.INPUT_SIZE)
            img = np.array(img)

        # Normalize ke [0, 1]
        img = img.astype(np.float32) / 255.0

        # ImageNet normalization
        mean = np.array(self.IMAGENET_MEAN, dtype=np.float32)
        std  = np.array(self.IMAGENET_STD,  dtype=np.float32)
        img  = (img - mean) / std

        # HWC → CHW → batch
        tensor = torch.from_numpy(img.transpose(2, 0, 1)).unsqueeze(0)
        return tensor.to(self.device)

    def predict(self, image_path: str) -> dict:
        """
        Jalankan inferensi neural network murni pada gambar dengan kalibrasi probabilitas.
        """
        # Muat ulang model jika ada file model baru di disk
        if self.model_path.exists():
            try:
                current_mtime = self.model_path.stat().st_mtime
                if current_mtime > self.last_loaded_time:
                    logger.info("Mendeteksi file model baru di disk. Melakukan reload...")
                    self._load_model()
            except Exception as e:
                logger.warning(f"Gagal memeriksa waktu modifikasi model: {e}")

        if self.model is None:
            logger.error("Model tidak tersedia, mengembalikan hasil dummy.")
            return self._dummy_result()

        try:
            import torch
            import torch.nn.functional as F
            import math

            tensor = self._preprocess_opencv(image_path)

            with torch.no_grad():
                raw_logits = self.model(tensor)
                # Terapkan Temperature Scaling agar nilai probabilitas terkalibrasi proporsional
                calibrated_logits = raw_logits / self.TEMPERATURE
                probabilities = F.softmax(calibrated_logits, dim=1).squeeze()

            probs_dict = {
                label: round(float(prob), 4)
                for label, prob in zip(self.class_labels, probabilities)
            }

            best_idx = int(probabilities.argmax().item())
            confidence = float(probabilities[best_idx])

            # Entropi distribusi untuk deteksi gambar non-lele (Out of Domain)
            entropy = -sum(
                float(p) * math.log(float(p) + 1e-9)
                for p in probabilities
            )
            max_entropy = math.log(len(self.class_labels))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

            # Deteksi Out of Domain (gambar bukan lele / objek lain)
            # Gambar lele memiliki keyakinan tinggi (>= 80%) & entropi rendah (<= 0.45)
            # Gambar bukan lele memiliki keyakinan rendah (< 65%) & entropi tinggi (> 0.65)
            if confidence < 0.65 or normalized_entropy > 0.65:
                logger.info(
                    f"Ketidakpastian tinggi: confidence={round(confidence*100,1)}% "
                    f"entropy={round(normalized_entropy,3)} → 'Bukan Lele'."
                )
                return {
                    "label": "Bukan Lele",
                    "confidence": round(confidence, 4),
                    "all_probabilities": probs_dict,
                }

            return {
                "label": self.class_labels[best_idx],
                "confidence": round(confidence, 4),
                "all_probabilities": probs_dict,
            }

        except Exception as e:
            logger.error(f"Error saat inferensi pada {image_path}: {e}")
            raise

    def _dummy_result(self) -> dict:
        return {
            "label": "Sehat",
            "confidence": 0.0,
            "all_probabilities": {label: 0.0 for label in self.class_labels},
        }


def get_classifier() -> LeleClassifier:
    """Singleton accessor — model hanya di-load sekali per proses worker."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = LeleClassifier()
    return _classifier_instance
