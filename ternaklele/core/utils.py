"""Utility functions untuk Ternak Lele."""
import os
import uuid
from PIL import Image as PilImage


def generate_unique_filename(original_name: str) -> str:
    """Generate nama file unik dengan UUID untuk menghindari collision."""
    ext = os.path.splitext(original_name)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def validate_image_file(file) -> tuple[bool, str]:
    """
    Validasi file gambar menggunakan Pillow.
    Returns: (is_valid, error_message)
    """
    allowed_formats = {"JPEG", "PNG", "WEBP"}
    max_size_mb = 10

    if file.size > max_size_mb * 1024 * 1024:
        return False, f"Ukuran gambar maksimal {max_size_mb}MB."

    try:
        img = PilImage.open(file)
        img.verify()
        file.seek(0)
        img = PilImage.open(file)
        if img.format not in allowed_formats:
            return False, f"Format tidak didukung. Gunakan: {', '.join(allowed_formats)}."
        file.seek(0)
        return True, ""
    except Exception:
        return False, "File bukan gambar yang valid."
