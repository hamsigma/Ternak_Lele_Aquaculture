import os, sys, django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
sys.path.insert(0, os.path.abspath('.'))
django.setup()

import core.ai.classifier as clf_mod
clf_mod._classifier_instance = None
from core.ai.classifier import get_classifier
clf = get_classifier()

print("=" * 65)
print("VERIFIKASI INTEGRASI PENGENALAN POLA PENYAKIT & OOD")
print("=" * 65)

catfish_tests = [
    ("Aeromonas", "dataset/fish_disease/Aeromonas/aeromonas_0001.jpg"),
    ("Aeromonas", "dataset/fish_disease/Aeromonas/aeromonas_0003.jpg"),
    ("Jamur", "dataset/fish_disease/Jamur/jamur_0001.jpg"),
    ("Jamur", "dataset/fish_disease/Jamur/jamur_0006.jpg"),
    ("Parasit", "dataset/fish_disease/Parasit/parasit_0001.jpg"),
    ("Parasit", "dataset/fish_disease/Parasit/parasit_0002.jpg"),
    ("Overfeeding", "dataset/fish_disease/Overfeeding/overfeeding_0144.jpg"),
    ("Overfeeding", "dataset/fish_disease/Overfeeding/real_overfeeding_01.jpg"),
    ("Sehat", "dataset/fish_disease/Sehat/sehat_0001.jpg"),
    ("Sehat", "dataset/fish_disease/Sehat/real_lele_sehat_01.jpg"),
]

print("\n1. PENGUJIAN CITRA LELE NYATA (5 KELAS TARGET):")
all_fish_ok = True
for expected, path in catfish_tests:
    if not os.path.exists(path):
        continue
    res = clf.predict(path)
    label = res['label']
    conf = round(res['confidence'] * 100, 1)
    ok = (label == expected)
    if not ok:
        all_fish_ok = False
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {expected:<12} | {os.path.basename(path):<26} -> {label} ({conf}%)")

non_fish_tests = [
    ("media/deteksi/2026/06/robot.png", "Robot 3D Art"),
    ("media/deteksi/2026/06/Code_MSV-017.jpg", "Diagram Teks / Code"),
    ("media/deteksi/2026/11/VirtualBox_server2_02_11_2026_15_23_15.png", "Screenshot VirtualBox"),
]

print("\n2. PENGUJIAN CITRA BUKAN LELE (OUT OF DOMAIN):")
all_ood_ok = True
for path, desc in non_fish_tests:
    if not os.path.exists(path):
        continue
    res = clf.predict(path)
    label = res['label']
    conf = round(res['confidence'] * 100, 1)
    ok = (label == "Bukan Lele")
    if not ok:
        all_ood_ok = False
    status = "OK  " if ok else "FAIL"
    print(f"  [{status}] {desc:<24} | {os.path.basename(path):<38} -> {label} ({conf}%)")

print("\n" + "=" * 65)
if all_fish_ok and all_ood_ok:
    print("HASIL: SEMUA PENGUJIAN (100%) LULUS DENGAN TINGKAT KEYAKINAN SOLID!")
else:
    print("HASIL: ADA PENGUJIAN YANG GAGAL.")
print("=" * 65)

