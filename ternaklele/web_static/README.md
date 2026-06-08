# Ternak Lele — Smart Aquaculture System (Static Web SPA Version)

Repositori ini berisi versi **Static Web SPA (Single Page Application)** dari platform Smart Aquaculture System (Ternak Lele). Versi ini dirancang untuk dijalankan sepenuhnya secara offline di sisi browser (*client-side*) tanpa memerlukan server Django, database PostgreSQL/SQLite, ataupun dependensi Python/PyTorch.

Sangat cocok untuk:
- Portfolio showcase / demonstrasi langsung.
- Deployment cepat ke layanan static hosting seperti **GitHub Pages**, **Vercel**, **Netlify**, atau **Cloudflare Pages**.
- Uji coba responsivitas antarmuka glassmorphism secara instan.

---

## 🌟 Fitur Simulasi
1. **Autentikasi (Daftar & Masuk)**: Mendukung simulasi pendaftaran dan login yang datanya tersimpan sementara di `localStorage`.
2. **Deteksi AI Ikan Lele**: Mensimulasikan klasifikasi citra penyakit lele (*Aeromonas*, *Jamur*, *Malnutrisi*, *Overfeeding*, atau *Sehat*) lengkap dengan grafik persentase probabilitas, skor akurasi, dan rekomendasi penanganan obat.
3. **Chatbot Leli**: Asisten virtual budidaya lele dengan respon interaktif, indikator mengetik (*typing indicator*), dan penanganan luar konteks (*out-of-context router*).
4. **Direktori Edukasi**: Berisi artikel manajemen air, pakan, dan direktori penyakit lele yang terisi lengkap secara statis.
5. **Riwayat Deteksi**: Log deteksi yang diunggah akan otomatis tercatat dan tersimpan di riwayat menggunakan penyimpanan lokal browser (`localStorage`).

---

## 🚀 Cara Menjalankan Secara Lokal

Anda bisa menjalankan website ini tanpa instalasi apapun.

### Cara 1: Double-Click File (Paling Sederhana)
Cukup buka folder `web_static/` lalu klik dua kali pada file **`index.html`** untuk langsung membukanya di browser Google Chrome, Edge, Firefox, atau Safari.

### Cara 2: Menggunakan Python HTTP Server
Jika Anda memiliki Python terinstal di komputer, jalankan perintah berikut di terminal dari dalam direktori `web_static/`:
```bash
python -m http.server 8080
```
Lalu buka browser Anda di alamat: `http://localhost:8080/`

### Cara 3: Menggunakan Live Server (VS Code)
Jika menggunakan VS Code, instal ekstensi **Live Server**, lalu klik kanan pada file `index.html` dan pilih **Open with Live Server**.

---

