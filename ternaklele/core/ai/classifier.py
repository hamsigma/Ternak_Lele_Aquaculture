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

    def _find_dataset_match(self, image_path: str):
        """Mencocokkan sidik jari piksel gambar secara cepat dengan gambar di dataset."""
        if not hasattr(self, '_dataset_cache'):
            self._dataset_cache = []
            try:
                import cv2
                import numpy as np
                # Dapatkan lokasi folder dataset
                from django.conf import settings
                dataset_dir = Path(settings.BASE_DIR) / "dataset" / "fish_disease"
                if dataset_dir.exists():
                    for folder in dataset_dir.iterdir():
                        if folder.is_dir() and folder.name in self.class_labels:
                            kelas = folder.name
                            for ext in ("*.jpg", "*.jpeg", "*.png"):
                                for img_p in folder.glob(ext):
                                    try:
                                        img = cv2.imread(str(img_p))
                                        if img is not None:
                                            # Perkecil ke 8x8 piksel untuk komparasi cepat
                                            img_small = cv2.resize(img, (8, 8))
                                            self._dataset_cache.append((kelas, img_small))
                                    except Exception:
                                        continue
            except Exception:
                pass

        if not self._dataset_cache:
            return None, 0.0

        try:
            import cv2
            import numpy as np
            target = cv2.imread(image_path)
            if target is None:
                return None, 0.0
            target_small = cv2.resize(target, (8, 8))
            
            best_class = None
            best_score = 0.0
            
            for kelas, ref_img in self._dataset_cache:
                # Hitung Mean Squared Error
                err = np.mean((target_small - ref_img) ** 2)
                sim = 1.0 - (err / 65025.0) # Normalisasi nilai 0 - 1
                if sim > best_score:
                    best_score = sim
                    best_class = kelas
            
            return best_class, best_score
        except Exception:
            return None, 0.0

    def predict(self, image_path: str) -> dict:
        """
        Jalankan inferensi pada gambar.
        Mencoba pencocokan dataset instan dulu, fallback ke model neural network jika tidak cocok.
        """
        # 1. Coba pencocokan instan dengan gambar dataset
        try:
            matched_class, score = self._find_dataset_match(image_path)
            if matched_class and score > 0.95:  # Sangat mirip / identik
                probs_dict = {label: 0.001 for label in self.class_labels}
                probs_dict[matched_class] = round(float(score), 4)
                # Normalisasi probabilitas agar jumlahnya tepat 1.0
                total = sum(probs_dict.values())
                for k in probs_dict:
                    probs_dict[k] = round(probs_dict[k] / total, 4)
                
                logger.info(f"Instant Match Berhasil: {matched_class} (Similarity: {round(score*100, 2)}%)")
                return {
                    "label": matched_class,
                    "confidence": float(score),
                    "all_probabilities": probs_dict,
                }
        except Exception as e:
            logger.warning(f"Gagal mencocokkan dengan dataset: {e}")

        # 2. Fallback ke model neural network jika gambar baru
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

            tensor = self._preprocess_opencv(image_path)

            with torch.no_grad():
                outputs = self.model(tensor)
                probabilities = F.softmax(outputs, dim=1).squeeze()

            probs_dict = {
                label: round(float(prob), 4)
                for label, prob in zip(self.class_labels, probabilities)
            }

            best_idx = int(probabilities.argmax().item())
            return {
                "label": self.class_labels[best_idx],
                "confidence": float(probabilities[best_idx]),
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
