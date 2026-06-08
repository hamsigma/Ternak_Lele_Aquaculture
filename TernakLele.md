# PRD & SRS PLATFORM "TERNAK LELE"
## Spesifikasi Sistem Berbasis Python Django Web Framework dengan Integrasi Computer Vision & AI Agent

### Informasi Dokumen
* **Nama Proyek:** Ternak Lele (Smart Aquaculture Web System)
* **Framework Utama:** Python Django 5.x + Django REST Framework (DRF)
* **Versi Dokumen:** 1.1.0 (v2-Refined)
* **Tanggal Pembaruan:** 7 Juni 2026
* **Status Dokumen:** Approved for Development Stack

---

# 1. Product Requirement Document (PRD)

## 1.1 Pendahuluan & Latar Belakang
Budidaya ikan lele (*Clarias gariepinus*) merupakan salah satu komoditas akuakultur unggulan di Indonesia karena perputaran modal yang cepat dan permintaan pasar yang tinggi. Namun, tantangan terbesar pembudidaya lapangan adalah tingginya angka mortalitas bibit dan ikan dewasa akibat serangan penyakit serta manajemen kualitas air yang kurang optimal. Keterlambatan identifikasi gejala penyakit seringkali menyebabkan gagal panen massal.

Platform **"Ternak Lele"** dirancang sebagai solusi berbasis web terintegrasi yang menggabungkan basis data pengetahuan budidaya dengan kecerdasan buatan (AI). Mengingat inti dari inovasi produk ini mengandalkan ekosistem Python untuk pengolahan data ilmiah, kecerdasan buatan, dan pengenalan gambar (*computer vision*), maka platform ini diputuskan untuk dikembangkan menggunakan **Framework Django** sebagai tulang punggung arsitekturnya. Hal ini memastikan proses penyatuan antara logika bisnis web dan model kecerdasan buatan dapat berjalan secara organik tanpa hambatan integrasi antar-bahasa.

## 1.2 Visi & Sasaran Produk
* **Visi:** Menjadi ekosistem digital budidaya lele terbesar yang mampu menurunkan tingkat kegagalan panen hingga di bawah 10% melalui intervensi teknologi prediktif berbasis Python AI yang mudah diakses.
* **Sasaran Utama:** Menyediakan modul edukasi perawatan terstruktur, sistem deteksi penyakit instan berbasis unggah foto, pelacakan kesehatan berkala, dan asistensi 24/7 menggunakan kecerdasan buatan.

## 1.3 Target Pengguna & Kebutuhan Fitur
Pengguna utama platform ini adalah pembudidaya lele skala kecil hingga menengah yang membutuhkan akurasi informasi secara cepat di lapangan, serta pakar perikanan yang mengelola keabsahan data biomedis ikan lele melalui panel admin.

> **Pemilihan Teknologi Produk**
> Penggunaan framework Django dipilih demi mempercepat pengembangan MVP (*Minimum Viable Product*). Keberadaan Django Admin bawaan mempercepat implementasi modul manajemen edukasi bagi Pakar Perikanan tanpa perlu membangun dasbor manajemen konten dari nol.

---

# 2. Software Requirements Specification (SRS) - Django Architecture

## 2.1 Deskripsi Umum & Arsitektur Sistem
Platform Ternak Lele dibangun menggunakan arsitektur **Python Django Framework**. Logika backend diimplementasikan menggunakan arsitektur *Model-View-Template* (MVT) standar Django atau dapat dikonfigurasi menjadi *Decoupled Architecture* menggunakan **Django REST Framework (DRF)** untuk menyediakan API bagi Frontend modern.

Keunggulan utama arsitektur Django dalam sistem ini adalah kemampuan eksekusi pustaka data science dan AI secara *native*. Pustaka pengolah citra seperti OpenCV, serta runtime model inferensi AI seperti PyTorch atau TensorFlow dapat dimuat langsung di dalam siklus eksekusi thread Django (*Django Views*), sehingga mengurangi latensi komunikasi antar-server.

## 2.2 Kebutuhan Fungsional Berbasis Django (Functional Requirements)

| ID Kebutuhan | Nama Fitur | Spesifikasi & Implementasi Django Stack |
| :--- | :--- | :--- |
| **FR-AUTH-01** | Autentikasi Pengguna | Menggunakan paket bawaan `django.contrib.auth`. Mendukung pembatasan hak akses (*Role-Based Access Control*) untuk memisahkan Pembudidaya dan Pakar Perikanan. |
| **FR-ADM-01** | Dashboard Pakar/Admin | Memanfaatkan **Django Admin Site** yang dikustomisasi dengan tema kustom. Berfungsi untuk entry data penyakit, obat-obatan, dan melakukan validasi kebenaran prediksi AI. |
| **FR-AI-01** | Deteksi Gambar Instan | Sistem menerima unggahan berkas via Django `FileField`. Berkas gambar divalidasi formatnya menggunakan pustaka Python Pillow sebelum dilempar ke pipeline inferensi Computer Vision. |
| **FR-AI-02** | Output Analisis Gambar | Django Views mengeksekusi skrip model klasifikasi penyakit lele, memformat hasil probabilitas ke dalam objek JSON/Konteks Template, dan menampilkannya kepada pengguna $\le$ 3 detik. |
| **FR-CHAT-01** | Asisten Chatbot AI | Integrasi pustaka Python `LangChain` atau SDK LLM langsung di dalam Django backend. Proses pencarian semantik data penanganan penyakit memanfaatkan database vektor yang dihubungkan ke Django ORM. |

## 2.3 Spesifikasi Algoritma & Komponen AI

### A. Klasifikasi dan Deteksi Penyakit Citra
Model visi komputer menggunakan arsitektur deep learning *EfficientNet-B3* yang di-host langsung dalam memori worker backend atau dieksekusi secara asinkronus menggunakan **Celery Task Runner** berbasis Python jika antrean unggahan padat. Nilai presisi matematika dari model ditargetkan memenuhi kriteria:

$$	ext{Precision} = rac{	ext{TP}}{	ext{TP} + 	ext{FP}} \ge 0.88$$

### B. Pipeline Chatbot & RAG
Setiap pesan teks yang masuk melalui antarmuka web ditangkap oleh Django API View, dikonversi menjadi data vektor (*embedding*), dan dicocokkan dengan dokumen pengetahuan budidaya lele menggunakan kueri SQL khusus pada ekstensi PostgreSQL `pgvector` yang dikelola secara langsung melalui migrasi bawaan Django ORM.

## 2.4 Kebutuhan Non-Fungsional (Non-Functional Requirements)

| Parameter | Spesifikasi Kebutuhan Teknis Django |
| :--- | :--- |
| **Performa (Performance)** | Manajemen aset statis menggunakan WhiteNoise atau AWS S3 via `django-storages`. Kecepatan query database dioptimalkan melalui metode Django ORM `select_related` dan `prefetch_related` untuk menjaga respons API $\le$ 500ms. |
| **Keamanan (Security)** | Proteksi bawaan terhadap SQL Injection melalui Django ORM parameterized queries. Aktivasi middleware `CsrfViewMiddleware` untuk menangani serangan Cross-Site Request Forgery dan `XFrameOptionsMiddleware` untuk mencegah clickjacking. |
| **Skalabilitas** | Dukungan penuh containerization menggunakan Docker untuk pembungkusan environment Django, Python, dan dependensi sistem C++ (OpenCV), sehingga mudah di-scale ke arsitektur cloud. |

## 2.5 Skema Data Awal (Django ORM Models Description)
Representasi entitas data didefinisikan secara langsung melalui kelas-kelas Python Model di Django yang kemudian ditranslasikan otomatis menjadi tabel PostgreSQL:

* **Class User(AbstractUser):** `id`, `nama`, `lokasi_kolam`, `no_telepon`, `tanggal_registrasi`.
* **Class DetectionLog(models.Model):** `id`, `user` (ForeignKey), `image` (ImageField), `penyakit_terdeteksi` (CharField), `confidence_score` (FloatField), `status_validasi` (BooleanField), `rekomendasi_penanganan` (TextField), `created_at` (DateTimeField).
* **Class ChatSession(models.Model):** `id`, `user` (ForeignKey), `context_summary` (CharField), `created_at`, `updated_at`.
* **Class ChatMessage(models.Model):** `id`, `session` (ForeignKey), `sender_type` (CharField), `message_text` (TextField), `created_at`.

## 2.6 Alur Pemrosesan Data Gambar pada Django Backend
1. Pengguna mengunggah gambar ikan lele lewat form HTML/React Frontend.
2. Request diterima oleh Django View, lalu divalidasi keamanannya oleh komponen middleware bawaan.
3. File disimpan temporer di media storage, lalu path file dikirimkan ke modul AI internal berbasis Python.
4. OpenCV memotong gambar (*preprocessing*) dan memuat model AI untuk kalkulasi klasifikasi penyakit.
5. Hasil diagnosis dikembalikan sebagai objek data Python, disimpan ke tabel database via Django ORM, dan dikirimkan kembali ke pengguna sebagai response fungsional web.
