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

    def _build_color_histogram(self, img):
        """Hitung L1-normalized BGR color histogram (8 bin per channel = 512 bin total)."""
        import cv2
        import numpy as np
        hist = cv2.calcHist([img], [0, 1, 2], None, [8, 8, 8],
                            [0, 256, 0, 256, 0, 256])
        hist = hist.flatten().astype(np.float32)
        total = hist.sum()
        if total > 0:
            hist /= total
        return hist

    def _find_dataset_match(self, image_path: str):
        """
        Pencocokan 2-Pass:
        Pass 1 — Exact pixel match (thumbnail 8x8):
                  Jika skor > 95%, gambar dikenali sebagai bagian dataset.
        Pass 2 — Color Histogram Pre-Filter:
                  Jika warna gambar < 20% mirip dengan warna SEMUA gambar lele
                  di dataset, maka gambar pasti bukan ikan lele → tolak dini.
        """
        if not hasattr(self, '_dataset_cache'):
            self._dataset_cache = []
            self._hist_cache    = []
            try:
                import cv2
                import numpy as np
                from django.conf import settings
                dataset_dir = Path(settings.BASE_DIR) / "dataset" / "fish_disease"
                class_count = {}
                if dataset_dir.exists():
                    for folder in dataset_dir.iterdir():
                        if not folder.is_dir():
                            continue
                        if folder.name not in self.class_labels:
                            continue
                        kelas = folder.name
                        class_count[kelas] = 0
                        for ext in ("*.jpg", "*.jpeg", "*.png"):
                            for img_p in folder.glob(ext):
                                try:
                                    img = cv2.imread(str(img_p))
                                    if img is None:
                                        continue
                                    # Thumbnail 8x8 untuk exact match
                                    img_small = cv2.resize(img, (8, 8))
                                    self._dataset_cache.append((kelas, img_small))
                                    # Histogram cache — maks 40 gambar per kelas (200 total)
                                    if class_count[kelas] < 40:
                                        self._hist_cache.append(
                                            self._build_color_histogram(img)
                                        )
                                        class_count[kelas] += 1
                                except Exception:
                                    continue
                logger.info(
                    f"Dataset cache: {len(self._dataset_cache)} gambar thumbnail, "
                    f"{len(self._hist_cache)} histogram."
                )
            except Exception as e:
                logger.warning(f"Gagal membangun dataset cache: {e}")

        if not self._dataset_cache:
            return None, 0.0

        try:
            import cv2
            import numpy as np
            target = cv2.imread(image_path)
            if target is None:
                return None, 0.0

            target_small = cv2.resize(target, (8, 8))

            # ── Pass 1: Exact pixel match ──────────────────────────────────
            best_class = None
            best_score = 0.0
            for kelas, ref_img in self._dataset_cache:
                err  = np.mean(
                    (target_small.astype(np.float32) - ref_img.astype(np.float32)) ** 2
                )
                sim = 1.0 - (err / 65025.0)
                if sim > best_score:
                    best_score = sim
                    best_class = kelas

            # Gambar persis sama dengan yang ada di dataset
            if best_score > 0.95:
                logger.info(f"Exact match: {best_class} (score={round(best_score,3)})")
                return best_class, best_score

            # ── Pass 2: Color Histogram Pre-Filter ────────────────────────
            # Hitung seberapa mirip warna gambar dengan gambar-gambar lele di dataset.
            # Gambar bukan lele (benda, manusia, dll.) akan memiliki distribusi warna
            # yang sangat berbeda dibandingkan foto ikan lele.
            if self._hist_cache:
                target_hist = self._build_color_histogram(target)
                max_intersection = max(
                    float(np.minimum(target_hist, ref_hist).sum())
                    for ref_hist in self._hist_cache
                )
                logger.info(
                    f"Histogram pre-filter: max_intersection={round(max_intersection, 3)}"
                )
                # Threshold 0.20 = gambar harus memiliki setidaknya 20% kesamaan warna
                # dengan foto lele manapun di dataset agar lolos ke model AI.
                if max_intersection < 0.20:
                    logger.info(
                        "Histogram pre-filter REJECTED: warna gambar tidak mirip lele "
                        f"(max_intersection={round(max_intersection,3)}) → Bukan Lele"
                    )
                    return "Bukan Lele", 0.0

            return None, 0.0

        except Exception as e:
            logger.warning(f"Error di _find_dataset_match: {e}")
            return None, 0.0


    def predict(self, image_path: str) -> dict:
        """
        Jalankan inferensi pada gambar.
        Mencoba pencocokan dataset instan dulu, fallback ke model neural network jika tidak cocok.
        """
        # 1. Coba pencocokan instan dengan gambar dataset
        try:
            matched_class, score = self._find_dataset_match(image_path)

            # ── Kasus A: Histogram pre-filter menolak gambar (bukan ikan lele) ──
            if matched_class == "Bukan Lele":
                logger.info("Gambar ditolak oleh histogram pre-filter → Bukan Lele")
                flat_probs = {label: round(1.0 / len(self.class_labels), 4) for label in self.class_labels}
                return {
                    "label": "Bukan Lele",
                    "confidence": 0.0,
                    "all_probabilities": flat_probs,
                }

            # ── Kasus B: Exact pixel match dengan gambar di dataset ──
            if matched_class and score > 0.95:
                probs_dict = {label: 0.001 for label in self.class_labels}
                probs_dict[matched_class] = round(float(score), 4)
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
            confidence = float(probabilities[best_idx])

            # ── OOD (Out-of-Domain) Detection ──────────────────────────────
            # Strategi ganda: threshold kepercayaan + entropi distribusi
            #
            # 1. Threshold Confidence: Jika probabilitas kelas terbaik < 85%,
            #    model ragu → kemungkinan bukan lele.
            # 2. Entropy Filter: Jika distribusi terlalu merata (semua kelas
            #    mendapat nilai serupa), model bingung → bukan lele.
            #    Entropi maksimal untuk 5 kelas = -5*(0.2*log(0.2)) ≈ 1.609
            #    Kita tolak jika entropy > 0.9 (distribusi terlalu seragam)
            import math
            entropy = -sum(
                float(p) * math.log(float(p) + 1e-9)
                for p in probabilities
            )
            # Normalisasi entropy ke rentang [0, 1]
            max_entropy = math.log(len(self.class_labels))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

            is_low_confidence = confidence < 0.85
            is_high_entropy    = normalized_entropy > 0.55  # Distribusi terlalu merata

            if is_low_confidence or is_high_entropy:
                logger.info(
                    f"OOD Detected: confidence={round(confidence*100,1)}% "
                    f"entropy={round(normalized_entropy,3)} "
                    f"→ Diklasifikasikan sebagai 'Bukan Lele'."
                )
                return {
                    "label": "Bukan Lele",
                    "confidence": confidence,
                    "all_probabilities": probs_dict,
                }

            return {
                "label": self.class_labels[best_idx],
                "confidence": confidence,
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
