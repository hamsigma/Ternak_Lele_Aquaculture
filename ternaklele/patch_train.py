"""Patch train.py agar support nama folder langsung (Sehat, Aeromonas, dll)"""
import os

path = "core/ai/train.py"
with open(path, encoding="utf-8") as f:
    content = f.read()

# Ganti fungsi remap_label agar support direct match
old = '''def remap_label(folder_name: str) -> str | None:
    """Petakan nama folder dataset ke label target Ternak Lele."""
    name_lower = folder_name.lower().replace(" ", "_")
    for key, target in LABEL_MAP.items():
        if key in name_lower:
            return target
    return None'''

new = '''def remap_label(folder_name: str) -> str | None:
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
    return None'''

if old in content:
    content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched train.py successfully")
else:
    print("Pattern not found, writing fallback patch")
    # Find and replace in a different way
    lines = content.split('\n')
    new_lines = []
    in_func = False
    skip_until_empty = False
    for i, line in enumerate(lines):
        if 'def remap_label' in line:
            in_func = True
            new_lines.append(line)
            new_lines.append('    """Petakan nama folder ke label Ternak Lele."""')
            new_lines.append('    if folder_name in TARGET_CLASSES:')
            new_lines.append('        return folder_name')
            new_lines.append('    name_lower = folder_name.lower().replace(" ", "_")')
            new_lines.append('    for key, target in LABEL_MAP.items():')
            new_lines.append('        if key in name_lower:')
            new_lines.append('            return target')
            new_lines.append('    return None')
            skip_until_empty = True
            continue
        if skip_until_empty:
            if line.strip() == '' or (line.strip() and not line.startswith(' ')):
                skip_until_empty = False
                if line.strip():
                    new_lines.append(line)
            continue
        new_lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))
    print("Wrote patched version")

print("Size now:", os.path.getsize(path))
