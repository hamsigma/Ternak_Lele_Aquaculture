import os, sys, glob, django

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.chdir(ROOT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()

from core.ai.classifier import get_classifier
clf = get_classifier()

print("=" * 60)
print("PENGUJIAN MODEL TERHADAP SAMPEL PER KELAS")
print("=" * 60)

classes = ['Aeromonas', 'Jamur', 'Parasit', 'Overfeeding', 'Sehat']
for c in classes:
    files = glob.glob(f'dataset/fish_disease/{c}/*.*')
    img_files = [f for f in files if f.lower().endswith(('.jpg', '.png', '.jpeg'))][:6]
    print(f"\n[{c}] ({len(files)} total files in dataset):")
    for f in img_files:
        try:
            res = clf.predict(f)
            lbl = res['label']
            conf = round(res['confidence'] * 100, 1)
            status = "MATCH" if lbl == c else "MISMATCH"
            print(f"  {status:<8} | {os.path.basename(f):<25} -> {lbl} ({conf}%)")
        except Exception as e:
            print(f"  ERROR    | {os.path.basename(f)}: {e}")

