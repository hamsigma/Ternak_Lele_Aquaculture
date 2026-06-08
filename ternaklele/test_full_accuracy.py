"""
Test Komprehensif Akurasi Klasifikasi AI
Menguji SEMUA gambar di dataset untuk mengukur akurasi nyata model.
"""
import django, os, sys, glob, time
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
sys.path.insert(0, '.')
django.setup()

# Reset singleton agar load model terbaru
import core.ai.classifier as clf_module
clf_module._classifier_instance = None

from core.ai.classifier import get_classifier

clf = get_classifier()
print('='*65)
print('  TEST KOMPREHENSIF KLASIFIKASI AI - Ternak Lele')
print('  Model loaded:', clf.model is not None)
print('  Device:', clf.device)
print('='*65)

test_classes = ['Sehat', 'Aeromonas', 'Malnutrisi', 'Jamur', 'Overfeeding']

# Per-class stats
class_correct = {}
class_total = {}
class_conf = {}
confusion = {}  # confusion[true][predicted] = count

for kelas in test_classes:
    class_correct[kelas] = 0
    class_total[kelas] = 0
    class_conf[kelas] = []
    confusion[kelas] = {}
    for k2 in test_classes:
        confusion[kelas][k2] = 0

total_correct = 0
total_tested = 0
errors = []

for kelas in test_classes:
    imgs = sorted(glob.glob('dataset/fish_disease/' + kelas + '/*.jpg'))
    imgs += sorted(glob.glob('dataset/fish_disease/' + kelas + '/*.png'))
    imgs += sorted(glob.glob('dataset/fish_disease/' + kelas + '/*.jpeg'))
    
    if not imgs:
        print('\n  [' + kelas + '] - tidak ada gambar')
        continue
    
    # Test semua gambar (max 50 per kelas)
    test_imgs = imgs[:50]
    print('\n--- ' + kelas + ' (' + str(len(test_imgs)) + ' gambar) ---')
    
    for img_path in test_imgs:
        try:
            hasil = clf.predict(img_path)
            label = hasil['label']
            conf = hasil['confidence']
            ok = label == kelas
            
            class_total[kelas] += 1
            total_tested += 1
            class_conf[kelas].append(conf)
            confusion[kelas][label] = confusion[kelas].get(label, 0) + 1
            
            if ok:
                class_correct[kelas] += 1
                total_correct += 1
                status = 'OK'
            else:
                status = 'MISS'
                errors.append((kelas, label, os.path.basename(img_path), conf))
            
            fname = os.path.basename(img_path)
            print('  ' + status + '  ' + fname + ' -> ' + label + ' (' + str(round(conf*100,1)) + '%)')
        except Exception as e:
            print('  ERROR: ' + str(e))

# Summary
print('\n' + '='*65)
print('  RINGKASAN AKURASI')
print('='*65)
print()

for kelas in test_classes:
    total = class_total[kelas]
    correct = class_correct[kelas]
    if total > 0:
        acc = correct / total * 100
        avg_conf = sum(class_conf[kelas]) / len(class_conf[kelas]) * 100
        print('  ' + kelas.ljust(15) + ': ' + str(correct) + '/' + str(total) + ' = ' + str(round(acc, 1)) + '% acc | Avg conf: ' + str(round(avg_conf, 1)) + '%')
    else:
        print('  ' + kelas.ljust(15) + ': Tidak ada data')

print()
if total_tested > 0:
    overall = total_correct / total_tested * 100
    print('  TOTAL AKURASI : ' + str(total_correct) + '/' + str(total_tested) + ' = ' + str(round(overall, 1)) + '%')
    
    if overall >= 90:
        print('  STATUS        : SANGAT BAIK - Siap produksi!')
    elif overall >= 80:
        print('  STATUS        : BAIK - Bisa digunakan.')
    elif overall >= 70:
        print('  STATUS        : CUKUP - Perlu peningkatan data.')
    else:
        print('  STATUS        : KURANG - Perlu training lebih lanjut.')

# Confusion matrix
print('\n' + '='*65)
print('  CONFUSION MATRIX')
print('='*65)
header = '  Actual\\Pred'.ljust(18)
for k in test_classes:
    header += k[:8].rjust(10)
print(header)
print('  ' + '-'*60)
for true_k in test_classes:
    row = '  ' + true_k[:15].ljust(16)
    for pred_k in test_classes:
        val = confusion[true_k].get(pred_k, 0)
        row += str(val).rjust(10)
    print(row)

# Error analysis
if errors:
    print('\n' + '='*65)
    print('  KESALAHAN PREDIKSI (' + str(len(errors)) + ' total)')
    print('='*65)
    for true_lbl, pred_lbl, fname, conf in errors[:20]:
        print('  ' + true_lbl + ' -> ' + pred_lbl + ' (' + str(round(conf*100,1)) + '%) | ' + fname)

print('\n' + '='*65)
