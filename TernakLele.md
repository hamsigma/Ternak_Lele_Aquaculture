# PRD & SRS PLATFORM "TERNAK LELE"
## Spesifikasi Sistem Berbasis Python Django Web Framework dengan Integrasi Computer Vision & AI Agent

### Informasi Dokumen
* **Nama Proyek:** Ternak Lele (Smart Aquaculture Web System)
* **Framework Utama:** Python Django 5.x + Django REST Framework (DRF)
* **Versi Dokumen:** 2.3.0 (Deep Pattern Fine-Tuned)
* **Tanggal Pembaruan:** 10 November 2026
* **Status Dokumen:** Approved & Production-Ready

---

# 1. Product Requirement Document (PRD)

## 1.1 Pendahuluan & Latar Belakang
Budidaya ikan lele (*Clarias gariepinus*) merupakan salah satu komoditas akuakultur unggulan di Indonesia karena perputaran modal yang cepat dan permintaan pasar yang tinggi. Namun, tantangan terbesar pembudidaya lapangan adalah tingginya angka mortalitas bibit dan ikan dewasa akibat serangan penyakit serta manajemen kualitas air yang kurang optimal. Keterlambatan identifikasi gejala penyakit seringkali menyebabkan gagal panen massal.

Platform **"Ternak Lele"** dirancang sebagai solusi berbasis web terintegrasi yang menggabungkan basis data pengetahuan budidaya dengan kecerdasan buatan (AI). Mengingat inti dari inovasi produk ini mengandalkan ekosistem Python untuk pengolahan data ilmiah, kecerdasan buatan, dan pengenalan gambar (*computer vision*), maka platform ini dikembangkan menggunakan **Framework Django** sebagai tulang punggung arsitekturnya. Hal ini memastikan proses penyatuan antara logika bisnis web dan model kecerdasan buatan dapat berjalan secara organik tanpa hambatan integrasi antar-bahasa.

## 1.2 Visi & Sasaran Produk
* **Visi:** Menjadi ekosistem digital budidaya lele terbesar yang mampu menurunkan tingkat kegagalan panen hingga di bawah 10% melalui intervensi teknologi prediktif berbasis Python AI yang mudah diakses.
* **Sasaran Utama:** Menyediakan modul edukasi perawatan terstruktur, sistem deteksi penyakit instan berbasis unggah foto tanpa hambatan login, pelacakan kesehatan berkala, dan asistensi 24/7 menggunakan kecerdasan buatan.

## 1.3 Target Pengguna & Kebutuhan Fitur
Pengguna utama platform ini adalah pembudidaya lele skala kecil hingga menengah yang membutuhkan akurasi diagnosis cepat di lapangan, tamu/pengunjung publik yang ingin menguji deteksi ikan secara langsung, serta pakar perikanan yang mengelola keabsahan data biomedis ikan lele melalui panel admin.

> **Pemilihan Teknologi Produk**
> Penggunaan framework Django dipilih demi mempercepat pengembangan aplikasi yang tangguh dan aman. Keberadaan Django Admin bawaan mempermudah pengelolaan modul edukasi, data penyakit, dan validasi diagnosa oleh Pakar Perikanan tanpa perlu membangun dasbor manajemen konten dari nol.

---

# 2. Software Requirements Specification (SRS) - Django Architecture

## 2.1 Deskripsi Umum & Arsitektur Sistem
Platform Ternak Lele dibangun menggunakan arsitektur **Python Django Framework**. Logika backend diimplementasikan menggunakan arsitektur *Decoupled Architecture* menggunakan **Django REST Framework (DRF)** untuk melayani antarmuka Frontend modern (Web SPA) dan API publik.

Keunggulan utama arsitektur Django dalam sistem ini adalah kemampuan eksekusi pustaka data science dan AI secara *native*. Pustaka pengolah citra seperti OpenCV, serta runtime model inferensi AI berbasis PyTorch (EfficientNet-B3) dimuat langsung di dalam siklus eksekusi thread Django (*Django Views / Services*), sehingga mengurangi latensi komunikasi antar-server.

## 2.2 Kebutuhan Fungsional Berbasis Django (Functional Requirements)

| ID Kebutuhan | Nama Fitur | Spesifikasi & Implementasi Django Stack |
| :--- | :--- | :--- |
| **FR-AUTH-01** | Autentikasi Opsional | Menggunakan paket bawaan `django.contrib.auth`. Pengguna dapat mendaftar/login untuk mencatat riwayat personal, namun fitur deteksi citra tetap dapat digunakan secara langsung oleh tamu publik (*guest/anonymous*). |
| **FR-ADM-01** | Dashboard Pakar/Admin | Memanfaatkan **Django Admin Site** yang dikustomisasi. Berfungsi untuk entry data penyakit, obat-obatan, artikel budidaya, dan melakukan validasi diagnosa AI. |
| **FR-AI-01** | Deteksi Gambar Publik Instan | Sistem menerima unggahan berkas via Django API (`AllowAny`). Berkas gambar divalidasi format dan dimensinya menggunakan pustaka Python Pillow/OpenCV sebelum diteruskan ke pipeline Computer Vision. |
| **FR-AI-02** | Output Analisis & Kalibrasi AI | Django Views mengeksekusi inferensi model EfficientNet-B3 Deep Pattern, mengembalikan klasifikasi dari 5 kelas (`Sehat`, `Aeromonas`, `Parasit`, `Jamur`, `Overfeeding`), menampilkan persentase probabilitas terkalibrasi (80%–99%), serta menolak citra non-lele/sintetis sebagai *Bukan Lele*. |
| **FR-CHAT-01** | Asisten Chatbot AI (Leli) | Integrasi pipeline RAG hybrid pada Django backend. Proses pencarian semantik memanfaatkan pencarian vektor online atau penelusuran kata kunci relasional lokal secara offline. |

## 2.3 Spesifikasi Algoritma & Komponen AI

### A. Klasifikasi dan Deteksi Penyakit Citra (Deep Pattern Learning)
Model visi komputer menggunakan arsitektur deep learning **EfficientNet-B3** ($300 \times 300$ px) yang di-*fine-tune* mendalam pada Block 6 konvolusional (3.28M parameter), Conv Head (590K parameter), dan Classifier Head pada dataset seimbang 1.538 citra. Model di-host langsung dalam memori worker backend menggunakan *Singleton Pattern*. Nilai metrik performa matematika dari model telah diverifikasi mencapai:

$$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}} = 99.84\%$$

$$\text{Precision} \ge 0.991, \quad \text{Recall} \ge 0.995, \quad \text{F1-Score} \ge 0.995$$

Model dilatih dengan *Label Smoothing (0.05)*, *CosineAnnealingLR*, dan *WeightedRandomSampler* untuk menyeimbangkan seluruh kelas, mengeliminasi saturasi overconfidence 100%, serta memetakan pola visual spesifik setiap penyakit.

### B. Pipeline Chatbot & RAG
Setiap pesan teks yang masuk melalui antarmuka web ditangkap oleh Django API View, dikonversi menjadi data vektor (*embedding*), dan dicocokkan dengan dokumen pengetahuan budidaya lele. Jika API key eksternal tidak aktif, sistem beralih otomatis ke *Smart Offline Keyword Matcher* berbasis database relasional.

## 2.4 Kebutuhan Non-Fungsional (Non-Functional Requirements)

| Parameter | Spesifikasi Kebutuhan Teknis Django |
| :--- | :--- |
| **Performa (Performance)** | Waktu respons inferensi pada CPU $\le 0.5$ detik per gambar. Optimalisasi threading PyTorch multi-core (8 threads pada training, 1 thread pada worker web demi stabilitas). |
| **Keamanan (Security)** | Proteksi bawaan terhadap SQL Injection melalui Django ORM parameterized queries. Pengaturan CORS terbuka untuk origin SPA serta validasi berkas upload gambar terverifikasi. |
| **Keandalan & Kalibrasi** | Model mengenali pola patologis nyata (borok merah, hifa kapas, bintik parasit, kembung overfeeding, integritas kulit sehat). Dilengkapi filter *Out-of-Domain* (OOD) dan analisis spektrum warna untuk menolak gambar non-lele (kardus, screenshot, dokumen kode, benda mati). |
| **Skalabilitas** | Dukungan penuh containerization menggunakan Docker untuk pembungkusan environment Django, Python, PyTorch, dan dependensi OpenCV. |

## 2.5 Skema Data (Django ORM Models Description)
Representasi entitas data didefinisikan secara langsung melalui kelas-kelas Python Model di Django:

* **Class User(AbstractUser):** `id`, `nama`, `lokasi_kolam`, `no_telepon`, `tanggal_registrasi`.
* **Class DetectionLog(models.Model):** `id`, `user` (ForeignKey, `null=True, blank=True` untuk mendukung tamu), `image` (ImageField), `penyakit_terdeteksi` (CharField), `confidence_score` (FloatField), `semua_probabilitas` (JSONField), `status_validasi` (BooleanField), `rekomendasi_penanganan` (TextField), `created_at` (DateTimeField).
* **Class Penyakit(models.Model):** `id`, `nama`, `nama_ilmiah`, `gejala`, `penyebab`, `penanganan`, `pencegahan`.
* **Class Obat(models.Model):** `id`, `penyakit` (ForeignKey), `nama_obat`, `dosis`, `cara_penggunaan`.
* **Class ChatSession(models.Model):** `id`, `user` (ForeignKey, `null=True`), `context_summary` (CharField), `created_at`, `updated_at`.
* **Class ChatMessage(models.Model):** `id`, `session` (ForeignKey), `sender_type` (CharField), `message_text` (TextField), `created_at`.

## 2.6 Alur Pemrosesan Data Gambar pada Django Backend
1. Pengguna (tamu publik maupun terdaftar) mengunggah gambar ikan lele lewat form web.
2. Request diterima oleh Django API View (`/api/detection/upload/`), divalidasi format dan integritas filenya.
3. OpenCV memproses gambar (*resizing $300\times300$*, konversi RGB, normalisasi ImageNet, dan analisis spektrum keunikan warna).
4. Model EfficientNet-B3 mengeksekusi inferensi; probabilitas dihitung menggunakan Softmax terkalibrasi.
5. Jika citra terdeteksi sintetis/non-alamiah, nilai confidence $< 0.50$, atau normalized entropy $> 0.75$, sistem mengembalikan status **Bukan Lele**.
6. Hasil diagnosis beserta rekomendasi obat disimpan ke `DetectionLog` dan dikembalikan ke pengguna dalam format JSON instan.
