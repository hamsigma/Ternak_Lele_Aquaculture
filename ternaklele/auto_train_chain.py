"""
Auto-chain trainer: tunggu quick_train selesai, lalu jalankan extended_train.
Run: python auto_train_chain.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
LOG  = ROOT / "train_log.txt"

print("="*60)
print("  AUTO TRAINING CHAIN")
print("  Fase 1: quick_train.py  (10 epoch, batch 8)")
print("  Fase 2: extended_train.py (30 epoch, batch 16)")
print("="*60)

# Cek apakah quick_train masih berjalan (dari PID file atau log)
# Kita cukup tunggu log selesai dengan memantau perubahan
last_epoch_seen = 0
print("\n[MONITOR] Memantau quick_train.py yang sedang berjalan...")
print("         (Ctrl+C untuk skip ke fase 2 secara manual)\n")

try:
    while True:
        if LOG.exists():
            content = LOG.read_text(errors='replace')
            # Cari baris epoch terakhir
            lines = [l for l in content.split('\n') if 'Epoch [' in l]
            if lines:
                last_line = lines[-1]
                # Cek apakah sudah epoch 10
                if 'Epoch [10/10]' in last_line:
                    print("[INFO] quick_train.py selesai (epoch 10/10 terdeteksi).")
                    break
                elif lines:
                    print(f"[STATUS] {last_line.strip()}", end='\r')
            # Cek apakah training selesai dengan marker
            if '==='  in content and 'Training Selesai' in content:
                print("[INFO] quick_train.py sudah selesai.")
                break
        time.sleep(30)
except KeyboardInterrupt:
    print("\n[SKIP] Manual skip ke fase 2.")

print("\n[FASE 2] Memulai extended_train.py (30 epoch, augmentasi agresif)...")
print("         Ini akan memakan waktu sekitar 5-8 jam di CPU.\n")

proc = subprocess.run(
    [sys.executable, "-u", "extended_train.py"],
    cwd=ROOT,
)

if proc.returncode == 0:
    print("\n[SELESAI] Extended training berhasil!")
else:
    print(f"\n[ERROR] Extended training keluar dengan kode: {proc.returncode}")
