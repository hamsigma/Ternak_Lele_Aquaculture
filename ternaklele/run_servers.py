import os
import subprocess
import sys
import time


def setup_database():
    """Jalankan migrasi dan seed database agar data penyakit selalu tersedia."""
    print("Menjalankan migrasi database...")
    subprocess.run(
        [sys.executable, "manage.py", "migrate", "--run-syncdb"],
        cwd=r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele"
    )
    print("Seeding data penyakit ke database...")
    subprocess.run(
        [sys.executable, "manage.py", "seed_penyakit"],
        cwd=r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele"
    )
    print("Database siap!\n")


def kill_port(port):
    print(f"Mengecek port {port}...")
    try:
        output = subprocess.check_output("netstat -ano", shell=True).decode('utf-8', errors='ignore')
        pids = set()
        for line in output.strip().split('\n'):
            if f":{port} " in line or f":{port} " in line.replace("  ", " "):
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) > 0:
                        pids.add(pid)
        for pid in pids:
            print(f"Mematikan proses PID {pid} pada port {port}...")
            os.system(f"taskkill /F /PID {pid}")
    except Exception as e:
        print(f"Gagal mengecek/mematikan port {port}: {e}")


# 1. Siapkan database (migrasi + seed)
setup_database()

# 2. Matikan server lama
kill_port(8000)
kill_port(8080)
time.sleep(1)

# 3. Jalankan Django server
print("Menjalankan Django backend (port 8000)...")
django_proc = subprocess.Popen(
    [sys.executable, "manage.py", "runserver", "0.0.0.0:8000"],
    cwd=r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele"
)

# 4. Jalankan Static SPA server
print("Menjalankan Static SPA frontend (port 8080)...")
spa_proc = subprocess.Popen(
    [sys.executable, "-m", "http.server", "8080"],
    cwd=r"c:\Users\Administrator\Documents\Tenak Lele\ternaklele\web_static"
)

print("\nKedua server berhasil dijalankan kembali!")
print("Backend: http://localhost:8000")
print("SPA Offline: http://localhost:8080")
print("\nTekan Ctrl+C di terminal ini untuk mematikan kedua server.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nMematikan server...")
    django_proc.terminate()
    spa_proc.terminate()
    print("Selesai.")
