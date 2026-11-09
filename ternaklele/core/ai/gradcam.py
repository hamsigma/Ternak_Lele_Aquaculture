"""
gradcam.py — Gradient-weighted Class Activation Mapping (Grad-CAM)
===================================================================
Menghasilkan visualisasi visual heatmap dari area spasial yang diperhatikan
oleh model EfficientNet-B3 saat membuat keputusan diagnosis.
Digunakan untuk memvalidasi apakah AI melihat patologi lele (borok, hifa, parasit,
kembung perut) atau hanya tertipu latar belakang (air kolam/ember/tangan).
"""

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None


class GradCAM:
    """
    Grad-CAM untuk EfficientNet-B3.
    Mengambil layer konvolusi terakhir (conv_head atau blocks[6]).
    """

    def __init__(self, model, target_layer=None):
        self.model = model
        self.target_layer = target_layer if target_layer is not None else model.conv_head
        self.gradients = None
        self.activations = None
        self._hook_handles = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, inp, out):
            self.activations = out.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        h1 = self.target_layer.register_forward_hook(forward_hook)
        h2 = self.target_layer.register_full_backward_hook(backward_hook)
        self._hook_handles.extend([h1, h2])

    def remove_hooks(self):
        for h in self._hook_handles:
            h.remove()
        self._hook_handles = []

    def generate_heatmap(self, tensor_input: torch.Tensor, target_class_idx: int = None) -> np.ndarray:
        """
        Menghasilkan heatmap normalisasi [0, 1] dengan ukuran spasial (H, W).
        """
        self.model.eval()
        self.model.zero_grad()

        # Tensor harus melacak gradien
        if not tensor_input.requires_grad:
            tensor_input = tensor_input.clone().detach().requires_grad_(True)

        with torch.enable_grad():
            output = self.model(tensor_input)
            if target_class_idx is None:
                target_class_idx = int(output.argmax(dim=1).item())
            
            score = output[0, target_class_idx]
            score.backward(retain_graph=True)

        # Global Average Pooling pada gradien
        weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)  # (1, C, 1, 1)
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # (1, 1, H, W)
        cam = F.relu(cam)

        # Interpolasi ke ukuran input tensor (300, 300)
        h_in, w_in = tensor_input.shape[2], tensor_input.shape[3]
        cam = F.interpolate(cam, size=(h_in, w_in), mode="bilinear", align_corners=False)
        cam_np = cam.squeeze().cpu().numpy()

        # Normalisasi ke rentang [0.0, 1.0]
        c_min, c_max = cam_np.min(), cam_np.max()
        if c_max > c_min:
            cam_norm = (cam_np - c_min) / (c_max - c_min)
        else:
            cam_norm = np.zeros_like(cam_np)

        return cam_norm, target_class_idx

    def overlay_heatmap_on_image(self, original_img_path: str, heatmap: np.ndarray, alpha: float = 0.45) -> np.ndarray:
        """
        Menggabungkan heatmap berwarna JET di atas citra asli menggunakan OpenCV / PIL.
        Mengembalikan array RGB uint8 (H, W, 3).
        """
        if cv2 is not None:
            orig_bgr = cv2.imread(original_img_path)
            if orig_bgr is None:
                orig_pil = Image.open(original_img_path).convert("RGB")
                orig_bgr = cv2.cvtColor(np.array(orig_pil), cv2.COLOR_RGB2BGR)

            h, w = orig_bgr.shape[:2]
            heatmap_resized = cv2.resize(heatmap, (w, h), interpolation=cv2.INTER_LINEAR)
            heatmap_uint8 = np.uint8(255 * heatmap_resized)
            colored_heatmap = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

            overlay = cv2.addWeighted(colored_heatmap, alpha, orig_bgr, 1 - alpha, 0)
            overlay_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            return overlay_rgb
        else:
            # Fallback tanpa OpenCV
            from matplotlib import cm
            orig_pil = Image.open(original_img_path).convert("RGBA")
            w, h = orig_pil.size
            cam_pil = Image.fromarray(np.uint8(255 * heatmap)).resize((w, h), Image.Resampling.BILINEAR)
            colormap = cm.get_cmap("jet")
            colored_cam = colormap(np.array(cam_pil) / 255.0)
            colored_cam_pil = Image.fromarray(np.uint8(colored_cam * 255)).convert("RGBA")
            blended = Image.blend(orig_pil, colored_cam_pil, alpha=alpha)
            return np.array(blended.convert("RGB"))

