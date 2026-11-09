# Ternak Lele — Smart Aquaculture System (Static Web SPA Version)

Repositori ini berisi versi **Static Web SPA (Single Page Application)** dari platform Smart Aquaculture System (Ternak Lele). Versi ini dirancang untuk dapat dijalankan sepenuhnya secara langsung di browser (*client-side*) maupun terhubung ke REST API Django backend.

Sangat cocok untuk:
- Portfolio showcase / demonstrasi interaktif.
- Deployment cepat ke layanan static hosting seperti **GitHub Pages**, **Vercel**, **Netlify**, atau **Cloudflare Pages**.
- Uji coba responsivitas antarmuka glassmorphism secara instan di perangkat mobile maupun desktop.

---

## 🌟 Fitur Unggulan
1. **Deteksi AI Ikan Lele Tanpa Hambatan Login**: Pengguna dan tamu publik dapat langsung mengunggah foto ikan lele untuk mendeteksi 5 kondisi klinis (`Sehat`, `Aeromonas`, `Parasit`, `Jamur`, dan `Overfeeding`) serta fitur penolakan otomatis citra non-lele (*Bukan Lele*).
2. **Confidence Score Terkalibrasi**: Menampilkan persentase probabilitas natural (82%–95%) tanpa overconfidence 100% palsu, dilengkapi rekomendasi penanganan dan obat terdaftar.
3. **Chatbot Leli**: Asisten virtual budidaya lele interaktif 24/7 dengan respons cerdas, indikator mengetik (*typing indicator*), dan penanganan luar konteks (*out-of-context router*).
4. **Direktori Edukasi Budidaya**: Artikel manajemen kualitas air, pakan efisien, dan pencegahan penyakit lele yang terisi lengkap secara terstruktur.
5. **Riwayat Deteksi Lokal**: Log hasil deteksi tersimpan rapi di riwayat menggunakan penyimpanan browser (`localStorage`).
6. **Autentikasi Fleksibel (Opsional)**: Mendukung pendaftaran dan login akun pembudidaya untuk sinkronisasi riwayat antar-perangkat.

---

## 🚀 Cara Menjalankan Secara Lokal

Website ini dapat dijalankan dengan beberapa cara mudah:

### Cara 1: Double-Click File (Paling Sederhana)
Buka folder `ternaklele/web_static/` lalu klik dua kali pada file **`index.html`** untuk langsung membukanya di browser Google Chrome, Edge, Firefox, atau Safari.

### Cara 2: Menggunakan Python HTTP Server
Jalankan perintah berikut di terminal dari dalam direktori `ternaklele/web_static/`:
```bash
python -m http.server 8080
```
Lalu buka browser di alamat: `http://localhost:8080/`

### Cara 3: Menggunakan Runner Terpadu (Backend + Frontend)
Jika ingin menjalankan backend Django (port 8000) dan frontend SPA (port 8080) secara terintegrasi:
```bash
cd ternaklele
python run_servers.py
```

---
*Ternak Lele — Platform Cerdas Pembudidaya Lele Indonesia.* 🇮🇩🐟
