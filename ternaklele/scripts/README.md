# Panduan Skrip Otomasi & Utilitas Proyek Ternak Lele

Direktori ini berisi skrip otomasi yang dikelompokkan secara terstruktur berdasarkan fungsinya:

```
ternaklele/scripts/
├── training/           # Skrip akuisisi dataset, augmentasi, & pelatihan model
├── evaluation/         # Skrip verifikasi metrik, pengujian inferensi, & pola
└── maintenance/        # Skrip pemeliharaan database, user, & sistem
```

---

## 1. Direktori `training/` (Pelatihan Model)

* **`train_rigorous.py`** *(Skrip Utama)*:
  * Melatih model **EfficientNet-B3** dengan protokol **Strict Zero-Leakage** (Pemisahan 75% Train, 15% Val, 10% Test berbasis ID subjek induk tanpa kontaminasi augmentasi).
  * Menghasilkan akurasi uji buta independen **96.12%**.
  * Cara menjalankan:
    ```bash
    python scripts/training/train_rigorous.py
    ```

* **`balance_overfeeding.py`**:
  * Melakukan augmentasi geometris terfokus (zoom perut, rotasi, kontras) khusus kelas `Overfeeding` agar seimbang dengan kelas lain.
  * Cara menjalankan:
    ```bash
    python scripts/training/balance_overfeeding.py
    ```

* **`build_and_clean_dataset.py`**:
  * Mengunduh, mengekstrak, dan membersihkan citra dataset dari Hugging Face dengan verifikasi integritas Pillow dan deduplikasi hash MD5.
  * Cara menjalankan:
    ```bash
    python scripts/training/build_and_clean_dataset.py
    ```

---

## 2. Direktori `evaluation/` (Pengujian & Evaluasi)

* **`verify_suite.py`** *(Suite Verifikasi Utama)*:
  * Menguji performa model terhadap 5 kelas patologis lele dan menguji penolakan citra non-ikan (*Out-of-Domain*).
  * Cara menjalankan:
    ```bash
    python scripts/evaluation/verify_suite.py
    ```

* **`test_patterns.py`**:
  * Menampilkan ringkasan prediksi dan keyakinan (*confidence*) sampel citra per kelas.
  * Cara menjalankan:
    ```bash
    python scripts/evaluation/test_patterns.py
    ```

* **`test_classifier.py`**:
  * Pengujian cepat fungsi inferensi modul `LeleClassifier`.
  * Cara menjalankan:
    ```bash
    python scripts/evaluation/test_classifier.py
    ```

* **`test_full_accuracy.py`**:
  * Evaluasi menyeluruh terhadap seluruh dataset lokal.
  * Cara menjalankan:
    ```bash
    python scripts/evaluation/test_full_accuracy.py
    ```

---

## 3. Direktori `maintenance/` (Pemeliharaan Sistem)

* **`reset_admin_password.py`**:
  * Mengatur ulang kata sandi superuser `admin` menjadi `admin123` untuk akses cepat ke Django Admin.
  * Cara menjalankan:
    ```bash
    python scripts/maintenance/reset_admin_password.py
    ```

* **`check_db.py`**:
  * Memeriksa daftar penyakit yang terdaftar di database SQLite dan menguji respons offline RAG chatbot.
  * Cara menjalankan:
    ```bash
    python scripts/maintenance/check_db.py
    ```

* **`delete_test_users.py`**:
  * Menghapus akun-akun pengguna testing dan menyisakan superuser bersih.
  * Cara menjalankan:
    ```bash
    python scripts/maintenance/delete_test_users.py
    ```

* **`print_chat.py`**:
  * Menampilkan 10 riwayat percakapan chatbot terakhir dari database.
  * Cara menjalankan:
    ```bash
    python scripts/maintenance/print_chat.py
    ```

