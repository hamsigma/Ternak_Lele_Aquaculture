import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
sys.path.insert(0, '.')
django.setup()

# Reset singleton agar load model terbaru
import core.ai.classifier as clf_module
clf_module._classifier_instance = None

print('=== TEST: Klasifikasi dengan Model Terbaru (98.5% val acc) ===')
from core.ai.classifier import get_classifier
import glob

clf = get_classifier()
print('Model loaded: ' + str(clf.model is not None))
print('Device: ' + str(clf.device))
print()

correct_count = 0
total = 0
test_classes = ['Aeromonas', 'Jamur', 'Overfeeding', 'Sehat', 'Malnutrisi']
for kelas in test_classes:
    imgs = glob.glob('dataset/fish_disease/' + kelas + '/*.jpg')
    if not imgs:
        print('  [' + kelas + '] - tidak ada gambar')
        continue
    # Test 3 gambar per kelas
    for img_path in imgs[:3]:
        try:
            hasil = clf.predict(img_path)
            label = hasil['label']
            conf = hasil['confidence']
            ok = label == kelas
            if ok:
                correct_count += 1
            total += 1
            status = 'OK  ' if ok else 'MISS'
            fname = os.path.basename(img_path)
            print('  ' + status + ' [' + kelas + '] ' + fname + ' -> ' + label + ' (' + str(round(conf*100,1)) + '%)')
        except Exception as e:
            print('  ERROR: ' + str(e))

print()
if total > 0:
    print('Akurasi sampel: ' + str(correct_count) + '/' + str(total) + ' = ' + str(round(correct_count/total*100,1)) + '%')
print('=== SELESAI ===')
