"""
Management command: python manage.py seed_penyakit
Mengisi database dengan data penyakit lele awal.
"""
from django.core.management.base import BaseCommand


PENYAKIT_DATA = [
    {
        "nama": "Aeromonas",
        "nama_ilmiah": "Aeromonas hydrophila",
        "deskripsi": "Penyakit bakterial paling umum pada lele, disebabkan bakteri gram-negatif Aeromonas hydrophila. Sangat menular dan dapat menyebabkan kematian massal.",
        "gejala": "Luka borok kemerahan pada kulit, perut kembung berisi cairan, sirip geripis, nafsu makan menurun, gerakan lemah dan berenang tidak normal, insang pucat.",
        "penyebab": "Bakteri Aeromonas hydrophila yang berkembang pesat pada kualitas air buruk, kepadatan tinggi, suhu air tidak stabil, dan stres akibat transportasi.",
        "penanganan": "Isolasi ikan sakit segera. Rendam dalam larutan garam NaCl 3-5% selama 5-10 menit. Pengobatan dengan antibiotik Oksitetrasiklin 50-75 mg/kg pakan selama 7-10 hari. Tambahkan vitamin C ke pakan untuk meningkatkan imunitas.",
        "pencegahan": "Jaga kualitas air (pH 6.5-8, DO >5 mg/L, suhu 26-30°C). Kurangi kepadatan tebar. Desinfeksi kolam sebelum tebar. Pemberian probiotik rutin.",
        "obat": [
            {"nama_obat": "Oksitetrasiklin", "dosis": "50-75 mg/kg pakan/hari", "cara_penggunaan": "Campurkan ke dalam pakan, berikan 2x sehari selama 7-10 hari.", "catatan": "Hentikan 2 minggu sebelum panen."},
            {"nama_obat": "Garam NaCl", "dosis": "30-50 gram per liter air", "cara_penggunaan": "Larutkan dalam air, rendam ikan selama 5-10 menit, ulangi 2-3 hari.", "catatan": "Untuk penanganan awal dan desinfeksi ringan."},
        ],
    },
    {
        "nama": "Malnutrisi",
        "nama_ilmiah": "Defisiensi Nutrisi Kronis",
        "deskripsi": "Kondisi kekurangan gizi kronis pada lele yang ditandai dengan kepala berukuran besar tidak proporsional dibanding badan yang kecil dan kurus. Terjadi akibat pakan tidak mencukupi kebutuhan nutrisi ikan.",
        "gejala": "Kepala tampak besar dan tidak proporsional dengan tubuh yang sangat kecil/kurus, tulang belakang terlihat menonjol, perut cekung, warna tubuh pucat, pertumbuhan sangat terhambat, ikan lamban dan mudah stres.",
        "penyebab": "Kekurangan pakan secara konsisten, kualitas pakan rendah (protein tidak mencukupi), persaingan pakan yang ketat akibat kepadatan tinggi, atau ikan lemah yang kalah bersaing mendapatkan pakan.",
        "penanganan": "Tingkatkan frekuensi pemberian pakan 3-4 kali sehari. Gunakan pakan dengan kandungan protein tinggi (30-35%). Pisahkan ikan kecil dari yang besar agar dapat pakan merata. Tambahkan suplemen vitamin dan mineral ke pakan.",
        "pencegahan": "Lakukan grading/sortasi ukuran ikan secara rutin. Berikan pakan sesuai kebutuhan (3-5% biomassa/hari). Gunakan pakan berkualitas dengan protein minimal 30%. Pastikan semua ikan mendapat jatah pakan yang sama.",
        "obat": [
            {"nama_obat": "Vitamin C (Asam Askorbat)", "dosis": "100-200 mg/kg pakan", "cara_penggunaan": "Campurkan ke pakan setiap hari untuk meningkatkan imunitas dan pemulihan.", "catatan": "Aman digunakan hingga panen."},
            {"nama_obat": "Suplemen Mineral Perikanan", "dosis": "2-3 g/kg pakan", "cara_penggunaan": "Campurkan ke pakan 3x seminggu selama masa pemulihan.", "catatan": "Tersedia di toko pertanian/perikanan."},
        ],
    },
    {
        "nama": "Jamur",
        "nama_ilmiah": "Saprolegnia sp. / Achlya sp.",
        "deskripsi": "Infeksi jamur (mikosis) pada lele, umumnya sebagai infeksi sekunder setelah luka bakterial. Ditandai pertumbuhan benang putih seperti kapas.",
        "gejala": "Pertumbuhan benang putih/abu-abu seperti kapas pada kulit, insang, atau telur. Ikan lemah, malas bergerak, nafsu makan turun. Luka di bawah hifa terlihat kemerahan.",
        "penyebab": "Jamur air Saprolegnia berkembang pada air dingin (<22°C), kualitas air buruk, bahan organik tinggi, dan ikan yang sudah lemah atau terluka.",
        "penanganan": "Naikkan suhu air ke 28-30°C. Rendam dengan larutan Malachite Green Oxalate 0.1 ppm selama 1 jam atau Methylene Blue 1-2 ppm. Ganti 50% air kolam. Tingkatkan aerasi.",
        "pencegahan": "Jaga suhu air di atas 26°C. Kurangi bahan organik di dasar kolam. Tidak overfeeding. Desinfeksi telur dengan Malachite Green sebelum penetasan.",
        "obat": [
            {"nama_obat": "Methylene Blue", "dosis": "1-2 mg/L (ppm)", "cara_penggunaan": "Larutkan dalam air kolam, diamkan 24 jam, lalu ganti sebagian air.", "catatan": "Aman untuk benih, hindari cahaya matahari langsung."},
            {"nama_obat": "Kalium Permanganat (KMnO4)", "dosis": "2-4 mg/L", "cara_penggunaan": "Larutkan dan rendam selama 30-60 menit, bilas dengan air bersih.", "catatan": "Hati-hati overdosis, dapat mematikan ikan."},
        ],
    },
    {
        "nama": "Overfeeding",
        "nama_ilmiah": "Gangguan Pencernaan / Digestive Disorder",
        "deskripsi": "Gangguan pencernaan akibat pemberian pakan berlebih (overfeeding) yang menyebabkan perut lele membuncit, terapung, dan tidak bisa berenang normal. Kondisi ini bisa mematikan jika tidak segera ditangani.",
        "gejala": "Perut sangat membuncit dan keras, ikan terapung atau berenang miring di permukaan, gerakan lamban dan tidak berkoordinasi, tidak mau makan, buang kotoran berlebihan atau tidak keluar, warna feses tidak normal (putih atau sangat gelap).",
        "penyebab": "Pemberian pakan melebihi kapasitas lambung ikan, pemberian pakan tidak terjadwal, pakan yang mengembang di dalam perut (pakan kering tanpa direndam), atau pakan yang sudah rusak/berjamur.",
        "penanganan": "Hentikan pemberian pakan selama 1-2 hari. Ganti 30-40% air kolam dengan air segar. Tambahkan probiotik ke air kolam. Berikan daun pepaya atau bawang putih yang dicincang ke dalam air sebagai stimulan pencernaan alami.",
        "pencegahan": "Atur jadwal pakan yang ketat (2-3x sehari). Berikan pakan secukupnya, amati sampai ikan berhenti makan aktif (±15 menit). Rendam pakan kering sebelum diberikan. Kurangi pakan saat cuaca panas atau hujan lebat.",
        "obat": [
            {"nama_obat": "Probiotik Perikanan", "dosis": "1-2 g/100L air kolam", "cara_penggunaan": "Larutkan dalam air, tuangkan ke kolam, ulangi 2-3 hari.", "catatan": "Bantu pemulihan bakteri pencernaan alami."},
            {"nama_obat": "Bawang Putih Cincang", "dosis": "5 gram/kg pakan atau 10 gram per 100L air", "cara_penggunaan": "Larutkan ekstrak di air kolam, biarkan 24 jam.", "catatan": "Stimulan pencernaan alami yang aman."},
        ],
    },
    {
        "nama": "Sehat",
        "nama_ilmiah": "-",
        "deskripsi": "Kondisi ikan lele yang sehat dan normal tanpa indikasi penyakit.",
        "gejala": "Tidak ada gejala penyakit. Ikan aktif, nafsu makan baik, warna tubuh normal, insang merah segar, tidak ada luka atau pertumbuhan abnormal.",
        "penyebab": "Tidak berlaku (kondisi normal).",
        "penanganan": "Pertahankan kualitas air optimal, berikan pakan bergizi seimbang, jaga kepadatan tebar, lakukan monitoring rutin.",
        "pencegahan": "Manajemen kolam baik: ganti air rutin 20-30% per minggu, probiotik, vitamin C, jaga pH 6.5-8, suhu 26-30°C, DO >5 mg/L.",
        "obat": [],
    },
]

ARTIKEL_DATA = [
    {
        "judul": "Manajemen Kualitas Air untuk Budidaya Lele Optimal",
        "kategori": "Manajemen Kolam",
        "konten": """Kualitas air adalah faktor paling kritis dalam budidaya lele. Parameter yang harus dijaga secara rutin:

**pH Air**
Lele tumbuh optimal pada pH 6.5-8.0. pH di bawah 6 atau di atas 9 dapat menyebabkan stres dan rentan penyakit. Gunakan kapur dolomit untuk menaikkan pH dan tawas untuk menurunkan.

**Oksigen Terlarut (DO)**
Minimal 4-5 mg/L. Tambahkan aerator jika DO turun. Tanda DO rendah: ikan naik ke permukaan dan megap-megap di pagi hari.

**Suhu**
Suhu optimal 26-30°C. Di bawah 22°C pertumbuhan melambat dan rentan jamur. Di atas 32°C ikan stres dan nafsu makan turun.

**Amonia (NH3)**
Harus di bawah 0.02 mg/L. Amonia tinggi dari kotoran ikan dan sisa pakan menyebabkan keracunan. Solusi: ganti air rutin, kurangi pakan, tambahkan probiotik.

**Penggantian Air**
Ganti 20-30% volume air setiap minggu. Saat musim panas atau kepadatan tinggi, ganti lebih sering. Air baru sebaiknya diendapkan dulu 24 jam.""",
        "penyakit_nama": None,
    },
    {
        "judul": "Panduan Pemberian Pakan Lele yang Efektif dan Efisien",
        "kategori": "Nutrisi & Pakan",
        "konten": """Pakan merupakan 60-70% dari total biaya operasional budidaya lele. Manajemen pakan yang tepat menentukan FCR (Feed Conversion Ratio) yang efisien.

**Frekuensi Pemberian Pakan**
Benih (<5 cm): 4-5 kali sehari
Fingerling (5-10 cm): 3-4 kali sehari  
Lele konsumsi (>10 cm): 2-3 kali sehari

**Jumlah Pakan**
Berikan pakan 3-5% dari biomassa total per hari. Evaluasi setiap 2 minggu dengan sampling berat ikan.

**Waktu Pemberian**
Hindari pemberian pakan tengah hari saat suhu paling tinggi. Optimal: pagi (06.00-07.00), sore (17.00-18.00), malam (21.00-22.00).

**Tanda Pakan Cukup**
Ikan masih aktif makan setelah 15-20 menit. Jika ada sisa pakan, kurangi jumlahnya karena sisa pakan meningkatkan amonia.

**Bahaya Overfeeding**
Pemberian pakan berlebih menyebabkan gangguan pencernaan (perut kembung) dan pencemaran air. Selalu amati respons ikan saat diberi pakan.

**Suplemen**
Vitamin C 100-200 mg/kg pakan meningkatkan imunitas. Probiotik 1-2 g/kg pakan memperbaiki pencernaan dan kualitas air.""",
        "penyakit_nama": None,
    },
    {
        "judul": "Cara Mencegah dan Mengatasi Penyakit Aeromonas pada Lele",
        "kategori": "Pengendalian Penyakit",
        "konten": """Aeromonas hydrophila adalah musuh utama pembudidaya lele. Penyakit ini bisa meludeskan seluruh kolam dalam hitungan hari jika tidak ditangani cepat.

**Deteksi Awal**
Perhatikan tanda-tanda: ikan berenang di permukaan, nafsu makan turun tiba-tiba, muncul luka kemerahan di tubuh. Segera isolasi ikan yang tampak sakit.

**Penanganan Darurat**
1. Isolasi ikan sakit ke wadah terpisah
2. Ganti 50% air kolam dengan air segar yang sudah diendapkan
3. Tambahkan garam NaCl 500 gram per 100 liter air (5 g/L)
4. Tingkatkan aerasi maksimal

**Pengobatan Medis**
Konsultasikan dengan dokter hewan atau penyuluh perikanan untuk penggunaan antibiotik. Oksitetrasiklin (OTC) 50 mg/kg pakan selama 7-10 hari adalah pilihan umum. Jangan gunakan antibiotik sembarangan karena dapat menimbulkan resistensi.

**Pencegahan Jangka Panjang**
- Probiotik Bacillus sp. 1-2 g/kg pakan 3x seminggu
- Bawang putih cincang 5 g/kg pakan sebagai antibakteri alami
- Vaksinasi (jika tersedia dari penyuluh setempat)
- Desinfeksi kolam dengan kapur tohor 200 kg/ha sebelum tebar""",
        "penyakit_nama": "Aeromonas",
    },
    {
        "judul": "Mengenali dan Menangani Malnutrisi pada Lele: Kepala Besar Badan Kecil",
        "kategori": "Pengendalian Penyakit",
        "konten": """Malnutrisi atau kekurangan gizi adalah masalah yang sering luput dari perhatian pembudidaya, namun bisa menyebabkan kerugian besar akibat pertumbuhan yang tidak seragam.

**Tanda-Tanda Malnutrisi**
Ikan lele yang mengalami malnutrisi akan menunjukkan kepala yang tampak besar dan tidak proporsional dibanding badannya yang kecil dan kurus. Tulang belakang terlihat menonjol, perut cekung, dan warna kulit pucat.

**Penyebab Utama**
- Kepadatan tebar terlalu tinggi sehingga ada ikan yang tidak kebagian pakan
- Kualitas pakan rendah (protein di bawah 25%)
- Frekuensi pakan terlalu jarang
- Ukuran lele tidak seragam sehingga yang kecil kalah bersaing

**Penanganan Segera**
1. Lakukan sortasi/grading untuk memisahkan ikan kecil dari yang besar
2. Berikan pakan protein tinggi (30-35%) 4x sehari untuk ikan yang malnutrisi
3. Tambahkan suplemen vitamin dan mineral
4. Kurangi kepadatan kolam

**Pencegahan**
Lakukan grading rutin setiap 2-3 minggu. Monitor FCR dan pertumbuhan rata-rata secara berkala.""",
        "penyakit_nama": "Malnutrisi",
    },
    {
        "judul": "Overfeeding dan Gangguan Pencernaan: Ancaman Tersembunyi di Kolam Lele",
        "kategori": "Pengendalian Penyakit",
        "konten": """Pemberian pakan berlebih (overfeeding) adalah kesalahan umum yang bisa mematikan ikan lele dalam waktu singkat akibat gangguan pencernaan akut.

**Gejala yang Harus Diwaspadai**
- Perut lele tampak sangat membuncit dan keras
- Ikan terapung atau berenang miring di permukaan
- Ikan tidak mau makan sama sekali
- Feses berwarna putih atau sangat gelap dan berlendir

**Mengapa Berbahaya?**
Pakan yang berlebih mengembang di dalam lambung dan usus ikan, menekan organ dalam, menghalangi aliran darah, dan menyebabkan kerusakan permanen pada sistem pencernaan. Dalam 24-48 jam, ikan bisa mati.

**Penanganan Cepat**
1. STOP pemberian pakan segera
2. Ganti 40-50% air kolam dengan air bersih
3. Tambahkan aerasi maksimal
4. Tuangkan probiotik ke kolam (1-2 g/100L)
5. Larutkan ekstrak bawang putih sebagai stimulan pencernaan

**Aturan Pemberian Pakan yang Aman**
- Berikan pakan yang habis dalam 10-15 menit
- Amati respons ikan — jika tidak aktif mengejar pakan, hentikan
- Jadwal ketat: tidak lebih dari 3x sehari untuk lele konsumsi""",
        "penyakit_nama": "Overfeeding",
    },
]


class Command(BaseCommand):
    help = "Mengisi database dengan data penyakit lele dan artikel edukasi awal."

    def handle(self, *args, **options):
        from apps.knowledge.models import Penyakit, Obat, ArtikelEdukasi

        self.stdout.write("Seeding data penyakit lele...")

        for data in PENYAKIT_DATA:
            obat_data = data.pop("obat", [])
            penyakit, created = Penyakit.objects.update_or_create(
                nama=data["nama"],
                defaults=data,
            )
            status = "dibuat" if created else "diperbarui"
            self.stdout.write(f"  [OK] Penyakit '{penyakit.nama}' {status}")

            # Hapus obat lama lalu buat ulang
            penyakit.obat_list.all().delete()
            for obat in obat_data:
                Obat.objects.create(penyakit=penyakit, **obat)

        # Hapus penyakit lama yang sudah tidak dipakai
        old_names = ["Bercak_Merah", "Parasit"]
        for old_name in old_names:
            deleted, _ = Penyakit.objects.filter(nama=old_name).delete()
            if deleted:
                self.stdout.write(f"  [HAPUS] Penyakit lama '{old_name}' dihapus")

        self.stdout.write("Seeding artikel edukasi...")

        for data in ARTIKEL_DATA:
            penyakit_nama = data.pop("penyakit_nama")
            penyakit = None
            if penyakit_nama:
                penyakit = Penyakit.objects.filter(nama=penyakit_nama).first()

            artikel, created = ArtikelEdukasi.objects.update_or_create(
                judul=data["judul"],
                defaults={**data, "penyakit": penyakit},
            )
            status = "dibuat" if created else "diperbarui"
            self.stdout.write(f"  [OK] Artikel '{artikel.judul[:50]}' {status}")

        self.stdout.write(self.style.SUCCESS(
            f"\nSelesai! {len(PENYAKIT_DATA)} penyakit, {len(ARTIKEL_DATA)} artikel."
        ))
