"""
Pipeline RAG (Retrieval-Augmented Generation) untuk Chatbot Ternak Lele.
Strategi:
  1. Coba OpenAI ChatGPT (jika API key tersedia)
  2. Fallback ke respons cerdas berbasis template + knowledge database
  3. Fallback terakhir: respons generik
"""
import logging
import re
from django.conf import settings

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Text Search pada Knowledge Base
# --------------------------------------------------------------------------- #

def _text_search(query: str, top_k: int = 5) -> list[str]:
    """Pencarian teks pada tabel Penyakit dan Artikel."""
    from apps.knowledge.models import Penyakit, ArtikelEdukasi

    results = []
    keywords = query.lower().split()

    # Cari penyakit berdasarkan nama, gejala, penyebab
    penyakit_qs = Penyakit.objects.none()
    for kw in keywords:
        if len(kw) > 3:  # skip kata pendek
            penyakit_qs = penyakit_qs | (
                Penyakit.objects.filter(nama__icontains=kw) |
                Penyakit.objects.filter(gejala__icontains=kw) |
                Penyakit.objects.filter(penyebab__icontains=kw) |
                Penyakit.objects.filter(penanganan__icontains=kw)
            )

    for p in penyakit_qs.distinct()[:top_k]:
        chunk = (
            f"[Penyakit: {p.nama}]\n"
            f"Nama Ilmiah: {p.nama_ilmiah or '-'}\n"
            f"Gejala: {p.gejala}\n"
            f"Penyebab: {p.penyebab}\n"
            f"Penanganan: {p.penanganan}\n"
            f"Pencegahan: {p.pencegahan}"
        )
        results.append(chunk)

    # Cari artikel
    artikel_qs = ArtikelEdukasi.objects.none()
    for kw in keywords:
        if len(kw) > 3:
            artikel_qs = artikel_qs | (
                ArtikelEdukasi.objects.filter(judul__icontains=kw) |
                ArtikelEdukasi.objects.filter(konten__icontains=kw)
            )

    for a in artikel_qs.distinct()[:2]:
        results.append(f"[Artikel: {a.judul}]\n{a.konten[:600]}")

    return results


def _get_all_penyakit() -> list:
    """Ambil semua data penyakit dari database."""
    from apps.knowledge.models import Penyakit
    return list(Penyakit.objects.prefetch_related("obat_list").all())


def get_knowledge_context(query: str, top_k: int = 4) -> str:
    """
    Ambil konteks relevan dari knowledge base.
    Prioritas: pgvector → fallback text search.
    """
    context_chunks = []

    # Coba semantic search dulu (hanya jika OpenAI tersedia)
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import OpenAIEmbeddings
            from pgvector.django import CosineDistance
            from apps.chatbot.vector_models import KnowledgeVector

            embedder = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
                timeout=2.0,  # Batasi timeout 2 detik agar tidak membekukan server saat offline
            )
            embedding = embedder.embed_query(query)
            results = (
                KnowledgeVector.objects
                .annotate(distance=CosineDistance("embedding", embedding))
                .order_by("distance")[:top_k]
            )
            context_chunks = [r.content for r in results]
        except Exception as e:
            logger.warning(f"pgvector search gagal: {e}")

    # Fallback ke text search
    if not context_chunks:
        context_chunks = _text_search(query, top_k)

    return "\n\n---\n\n".join(context_chunks)


# --------------------------------------------------------------------------- #
#  Smart Offline Responder (tanpa OpenAI)
# --------------------------------------------------------------------------- #
import random

PENYAKIT_KEYWORDS = {
    "aeromonas":    ["aeromonas", "borok", "luka", "bakteri", "bercak", "merah"],
    "malnutrisi":   ["malnutrisi", "gizi", "kepala besar", "kurus", "badan kecil"],
    "jamur":        ["jamur", "kapas", "putih", "saprolegnia", "fungi"],
    "overfeeding":  ["overfeeding", "kembung", "pencernaan", "pakan berlebih", "terapung", "perut besar"],
    "sehat":        ["sehat", "normal", "baik", "segar"],
}

GENERAL_KEYWORDS = {
    "pakan":       ["pakan", "makan", "feed", "nutrisi", "protein", "dosis pakan"],
    "air":         ["air", "ph", "oksigen", "kualitas air", "ganti air", "bersih", "amonia"],
    "kolam":       ["kolam", "terpal", "beton", "tanah", "persiapan", "luas"],
    "bibit":       ["bibit", "benih", "anakan", "tebar", "padat tebar"],
    "panen":       ["panen", "ukuran", "bobot", "waktu panen", "konsumsi"],
    "probiotik":   ["probiotik", "em4", "bakteri baik", "fermentasi"],
    "garam":       ["garam", "natrium", "sodium", "krosok"],
    "kanibal":     ["kanibal", "saling makan", "grading", "sortasi", "kepadatan", "ukuran beda"],
    "biaya":       ["biaya", "modal", "untung", "fcr", "keuntungan", "harga", "pasar"],
}


def _build_smart_response(query: str, knowledge_context: str) -> str:
    """
    Membangun respons cerdas berbasis template + knowledge context.
    Digunakan ketika OpenAI tidak tersedia.
    """
    q_lower = query.lower()

    # 1. DETEKSI PENYAKIT DETAIL (Kecuali Sehat)
    penyakit_match = None
    from apps.knowledge.models import Penyakit
    all_penyakit = Penyakit.objects.prefetch_related("obat_list").all()

    for p in all_penyakit:
        if p.nama.lower() != "sehat":
            if p.nama.lower().replace("_", " ") in q_lower or p.nama.lower() in q_lower:
                penyakit_match = p
                break

    if penyakit_match:
        p = penyakit_match
        obat_info = ""
        if p.obat_list.exists():
            obat_texts = []
            for o in p.obat_list.all():
                obat_texts.append(f"💊 **{o.nama_obat}** (Dosis: {o.dosis} | Cara: {o.cara_penggunaan})")
            obat_info = "\n\n**Rekomendasi Obat:**\n" + "\n".join(obat_texts)

        nama_tampil = p.nama.replace('_', ' ')
        return (
            f"Oh ya Kak, terkait penyakit **{nama_tampil}** ({p.nama_ilmiah or 'kondisi klinis'}), berikut Leli jelaskan detailnya:\n\n"
            f"⚠️ **Gejala yang Terlihat:**\n{p.gejala}\n\n"
            f"🔍 **Penyebab Utama:**\n{p.penyebab}\n\n"
            f"🛠️ **Langkah Penanganan:**\n{p.penanganan}\n\n"
            f"🛡️ **Cara Pencegahan:**\n{p.pencegahan}"
            f"{obat_info}\n\n"
            f"Saran Leli, segera pisahkan (isolasi) lele yang sakit ke wadah karantina ya Kak agar tidak menular ke lele sehat lainnya!"
        )

    # 2. KATEGORI BUDIDAYA UMUM (Conversational & Natural)
    for category, keywords in GENERAL_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            if category == "pakan":
                pakan_variations = [
                    "Wah, ngomongin soal pakan lele memang sangat penting Kak! Biar FCR-nya bagus dan cepat panen, ini tips dari Leli:\n\n"
                    "• **Frekuensi**: Berikan 2–3 kali sehari (pagi, sore, malam). Oh ya, malam hari porsinya bisa agak banyak karena lele aktif di malam hari!\n"
                    "• **Takaran**: Sekitar 3–5% dari total berat lele di kolam Kakak.\n"
                    "• **Protein**: Pilih pelet dengan protein minimal 30% biar dagingnya padat.\n"
                    "• **Bahaya Overfeeding**: Jangan sampai berlebihan ya Kak, karena sisa pakan yang mengendap di dasar kolam bisa jadi racun amonia dan bikin lele kembung/terapung.\n\n"
                    "Mau tanya resep pakan alternatif atau cara ngitung kebutuhan pakan hariannya, Kak?",
                    
                    "Nutrisi pakan menentukan kecepatan lele tumbuh besar Kak! Ini aturan main pakan dari Leli:\n\n"
                    "• **Bibit (di bawah 5cm)**: Beri pakan tipe tepung/fine-grain berulang 4-5 kali sehari dalam porsi kecil.\n"
                    "• **Lele Dewasa**: Beri pelet apung diameter sesuai bukaan mulut lele. Cukup 2-3 kali sehari.\n"
                    "• **Waktu Terbaik**: Pagi jam 7 dan sore jam 5. Hindari memberi makan saat matahari terik di jam 12-1 siang karena suhu panas menurunkan nafsu makan lele.\n\n"
                    "Mau konsultasi cara fermentasi pelet agar lele lebih mudah mencerna pakan, Kak?"
                ]
                return random.choice(pakan_variations)
                
            elif category == "air":
                air_variations = [
                    "Air kolam itu rumah bagi lele Kak, jadi kalau airnya bersih, lele pasti nyaman dan nafsu makan tinggi! Ini panduannya:\n\n"
                    "• **Kadar pH**: Jaga di kisaran 6.5 sampai 8.0. Kalau terlalu asam, lele gampang sakit.\n"
                    "• **Suhu**: Idealnya 25–30°C. Cuaca pancaroba biasanya bikin suhu tidak stabil.\n"
                    "• **Oksigen (DO)**: Minimal 3-5 mg/L. Kalau lele banyak megap-megap di permukaan pagi hari, itu tandanya kekurangan oksigen.\n"
                    "• **Solusi**: Lakukan penggantian air kolam sebanyak 20-30% secara berkala dan berikan probiotik EM4 untuk mengurai sisa kotoran.\n\n"
                    "Warna air kolam Kakak sekarang hijau, cokelat, atau hitam pekat?",
                    
                    "Kunci sukses budidaya lele itu sebenarnya di 'Manajemen Air' Kak. Lele yang sakit biasanya karena air kolamnya bermasalah. Leli sarankan:\n\n"
                    "1. **Buang Lumpur Dasar**: Endapan sisa pakan di dasar kolam menghasilkan gas amonia beracun. Buang secara rutin (sifon).\n"
                    "2. **Aplikasi Probiotik**: Masukkan probiotik 1-2 minggu sekali untuk mengurai sisa bahan organik.\n"
                    "3. **Ganti Air**: Jangan ganti seluruh air sekaligus! Cukup buang 20% air dasar kolam lalu isi air baru agar ikan tidak stres akibat perubahan suhu mendadak."
                ]
                return random.choice(air_variations)
                
            elif category == "kolam":
                return (
                    "Persiapan kolam yang matang itu kunci kesuksesan budidaya Kak! Ini tips mempersiapkannya:\n\n"
                    "1. **Jemur Kolam**: Keringkan kolam selama 3-5 hari biar bakteri jahat mati.\n"
                    "2. **Kapur Dolomit**: Taburkan 100-200 gram/m² untuk menetralkan pH tanah/dinding.\n"
                    "3. **Fermentasi Air**: Isi air setinggi 30-40 cm dulu, campurkan probiotik, lalu diamkan 5-7 hari sampai air berwarna kehijauan (tumbuh plankton alami).\n"
                    "4. **Ketinggian**: Setelah plankton tumbuh, tambahkan air sampai 80-100 cm baru tebar bibit.\n\n"
                    "Kolam Kakak tipe apa nih? Kolam terpal, semen, atau tanah?"
                )
            elif category == "bibit":
                return (
                    "Memilih bibit lele yang unggul bakal meminimalkan kematian dini Kak! Ini ciri-ciri bibit berkualitas:\n\n"
                    "• **Aktif**: Berenang lincah menantang arus air.\n"
                    "• **Seragam**: Ukuran tubuhnya mirip (misal 5-7 cm) biar tidak saling serang.\n"
                    "• **Fisik Sempurna**: Kulit mulus, kumis utuh, dan tidak ada luka.\n"
                    "• **Tips Tebar**: Jangan langsung dituang ya Kak! Apungkan wadah bibit di kolam selama 15 menit agar lele menyesuaikan diri dengan suhu air baru (aklimatisasi).\n\n"
                    "Ada rencana mau tebar berapa ribu ekor bibit, Kak?"
                )
            elif category == "panen":
                return (
                    "Momen panen pasti yang paling ditunggu-tunggu! Biar hasil panen Kakak melimpah dan untung maksimal, ini rahasianya:\n\n"
                    "• **Ukuran Pasar**: Biasanya isi 8-10 ekor per kilogram (panjang ±20 cm).\n"
                    "• **Waktu Budidaya**: Cukup 60-90 hari saja jika pakannya rajin dan berkualitas.\n"
                    "• **Tips Penting**: Puasakan lele selama 24 jam sebelum dipanen. Ini berguna biar lambung lele kosong, lele tidak gampang muntah, dan dagingnya segar/tidak amis saat dikirim!\n\n"
                    "Pemasarannya sudah aman kan Kak? Biasanya dijual ke tengkulak atau langsung ke warung pecel lele?"
                )
            elif category == "probiotik":
                return (
                    "Probiotik (seperti EM4 Perikanan atau Bacillus) sangat berguna untuk kesehatan pencernaan lele dan penguraian amonia di kolam Kak. Ini panduan menggunakannya:\n\n"
                    "• **Campur Pakan**: Larutkan 1 tutup botol EM4 + 1 sendok makan molase/gula dalam secangkir air. Bibiskan (semprotkan) secara merata ke 1 kg pelet, diamkan 15 menit agar meresap baru berikan ke lele.\n"
                    "• **Kualitas Air**: Tuangkan probiotik yang telah diaktifkan ke air kolam setiap 1-2 minggu sekali untuk menjaga kestabilan plankton baik.\n\n"
                    "Apakah Kakak sudah mulai memakai probiotik di kolam saat ini?"
                )
            elif category == "garam":
                return (
                    "Garam krosok (garam ikan non-yodium) adalah 'obat dewa' yang murah meriah untuk lele Kak! Kegunaannya meliputi:\n\n"
                    "1. **Pencegahan Stres**: Menjaga keseimbangan osmoregulasi lele saat ganti air kolam atau cuaca ekstrem.\n"
                    "2. **Desinfektan Alami**: Membunuh parasit kulit dan mencegah spora jamur tumbuh.\n"
                    "3. **Dosis Aman**: \n"
                    "   • Pencegahan: 500 gram sampai 1 kg garam per 1.000 liter air kolam.\n"
                    "   • Pengobatan Jamur: Rendam lele yang sakit dalam wadah khusus dengan dosis 10-20 gram garam per liter air selama 5-10 menit.\n\n"
                    "Pastikan menggunakan garam krosok kasar kasar ya Kak, jangan garam dapur beryodium!"
                )
            elif category == "kanibal":
                return (
                    "Masalah lele saling memakan (kanibalisme) biasanya dipicu oleh perbedaan ukuran yang mencolok atau pakan yang telat Kak. Solusi terbaik dari Leli:\n\n"
                    "1. **Grading / Sortasi**: Lakukan penyortiran ukuran lele secara rutin setiap 2 minggu sekali. Pisahkan lele yang berukuran bongsor, sedang, dan kerdil ke kolam berbeda.\n"
                    "2. **Pemberian Pakan Tepat Waktu**: Lele yang kelaparan akan langsung berburu kawannya yang lebih kecil. Jaga konsistensi jadwal makan lele.\n"
                    "3. **Padat Tebar yang Sesuai**: Jangan terlalu padat tebar (ideal bibit 100-150 ekor per m² pada air setinggi 80 cm) agar tingkat kompetisi ruang tidak terlalu tinggi.\n\n"
                    "Apakah lele Kakak saat ini ukurannya sudah mulai terlihat tidak seragam?"
                )
            elif category == "biaya":
                return (
                    "Mengelola pengeluaran modal budidaya lele itu penting agar Kakak bisa untung maksimal! Ini tips dari Leli:\n\n"
                    "• **Feed Conversion Ratio (FCR)**: Targetkan FCR di bawah 1.1. Artinya, untuk menghasilkan 1 kg daging lele, Kakak hanya butuh menghabiskan pelet maksimal 1.1 kg.\n"
                    "• **Pakan Alternatif**: Untuk menghemat biaya pakan komersial (pelet pabrik), Kakak bisa selingi dengan pakan alternatif berprotein tinggi seperti maggot BSF, ampas tahu fermentasi, atau ikan rucah rebus.\n"
                    "• **Biaya Bibit & Listrik**: Catat semua pengeluaran dari awal pembelian bibit, biaya listrik aerator/pompa air, hingga vitamin agar pembukuan panen Kakak rapi.\n\n"
                    "Berapa ukuran kolam Kakak dan berapa banyak bibit yang sedang dipelihara? Mari kita bantu hitung estimasi biayanya!"
                )

    # 3. KONDISI SEHAT (Sehat / Normal / Baik / Segar)
    sehat_keywords = PENYAKIT_KEYWORDS.get("sehat", ["sehat", "normal", "baik", "segar"])
    if any(sw in q_lower for sw in sehat_keywords):
        return (
            "Alhamdulillah! Senang sekali mendengarnya. Kondisi lele Kakak terpantau **Sehat** walafiat. 🐟💚\n\n"
            "Tetap pertahankan ya Kak! Jangan lupa rutin ganti air kolam sekitar 20-30% setiap minggu, berikan pakan berkualitas secara konsisten, dan selalu jaga kebersihan kolam."
        )

    # 4. PERKENALAN DIRI (Self-Introduction)
    intro_keywords = ["siapa kamu", "siapa leli", "kenalan", "nama kamu", "kamu siapa", "leli itu siapa", "leli siapa"]
    if any(kw in q_lower for kw in intro_keywords):
        intro_variations = [
            "Halo Kak! Kenalin, aku **Leli** (asisten AI ahli budidaya ikan lele) 🐟✨\n\n"
            "Aku diciptakan khusus untuk menemani Kakak dalam merawat kolam lele kesayangan. Kakak bisa tanya-tanya aku tentang:\n"
            "• **Diagnosis penyakit lele** (seperti Aeromonas, Jamur, Malnutrisi, atau Overfeeding)\n"
            "• **Tips pakan** yang hemat dan bergizi\n"
            "• **Menjaga kualitas air** biar lele nggak stres\n"
            "• **Persiapan kolam** dari awal tebar sampai panen raya!\n\n"
            "Ada yang bisa Leli bantu hari ini biar lele kita sehat dan cepat besar? 😊",
            
            "Hai Kak! Aku **Leli**, asisten budidaya lele pintar kamu di sini. 🐟👋\n\n"
            "Leli siap bantu Kakak memecahkan masalah kolam, mengoptimalkan pakan, mengenali gejala penyakit lele secara dini, hingga tips sortasi lele agar tidak saling kanibal.\n\n"
            "Apa yang ingin Kakak tanyakan hari ini?"
        ]
        return random.choice(intro_variations)

    # 5. SAPAAN UMUM (Common Greetings)
    greetings = ["halo", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum", "p", "permisi", "apa kabar"]
    if q_lower.strip() in greetings or any(q_lower.strip() == g for g in greetings) or any(q_lower.startswith(g + " ") for g in greetings):
        greeting_variations = [
            "Halo Kak! Senang banget bisa ketemu. 😊\n\n"
            "Semoga hari ini kolam lele Kakak dalam kondisi prima ya! Leli siap bantu jawab pertanyaan seputar budidaya, penyakit lele, pakan, atau kualitas air kolam. Kakak mau diskusi tentang apa hari ini?",
            
            "Hai Kak! Senang sekali menyapa Kakak hari ini. Bagaimana kondisi kolam lele Anda? 🐟✨\n\n"
            "Ada yang bisa Leli bantu? Tanyakan saja seputar pakan, persiapan kolam, air, atau penyakit lele ya!",
            
            "Halo Kak! Leli di sini siap menemani diskusi budidaya lele Anda. Semoga lele Anda tumbuh sehat dan nafsu makan kuat! Ada kendala apa di kolam hari ini? 😊"
        ]
        return random.choice(greeting_variations)

    # 6. JIKA ADA KONTEKS KNOWLEDGE RELEVAN DARI DATABASE
    if knowledge_context.strip():
        # Bersihkan format tag database agar enak dibaca
        clean_context = knowledge_context.replace("[Penyakit:", "📌 **Penyakit ").replace("[Artikel:", "📖 **Artikel ")
        return (
            "Berdasarkan catatan panduan Ternak Lele yang Leli temukan:\n\n"
            + clean_context
            + "\n\n---\n*Semoga informasi di atas membantu Kakak ya! Jika masih ragu, Kakak bisa menggunakan fitur Validasi Pakar di menu platform.*"
        )

    # 7. JAWABAN LUAR KONTEKS (Out of Context - Pintar & Menghibur)
    out_of_context_responses = [
        "siapa presiden", "cuaca", "berita", "politik", "rendang", "masak", 
        "sejarah", "games", "game", "main", "lagu", "musik", "film", "saham",
        "crypto", "belanja", "harga", "uang", "pacar", "cinta"
    ]
    if any(ow in q_lower for ow in out_of_context_responses) or len(q_lower.split()) > 4:
        out_of_context_variations = [
            "Wah, pertanyaan menarik Kak! 😄\n\n"
            "Sebenarnya, Leli adalah asisten khusus budidaya lele. Tapi kalau Kakak penasaran tentang itu, sepemahaman Leli, hal tersebut cukup ramai dibahas banyak orang akhir-akhir ini!\n\n"
            "Meskipun Leli ahli di dunia air dan kolam lele, kalau Kakak mau ngobrol santai Leli senang-senang saja. Tapi jangan lupa pantau kolam lelenya juga ya Kak! Ada kendala apa di kolam lele Kakak hari ini?",
            
            "Hehe, seru juga nih pertanyaannya Kak! 😆 Tapi sebagai asisten budidaya lele, Leli lebih mengerti tentang air kolam, bibit unggul, dan penyakit lele.\n\n"
            "Bagaimana kalau kita kembali membahas cara merawat lele agar cepat panen dan sehat walafiat? Kolam lele Kakak saat ini aman-aman saja kan?"
        ]
        return random.choice(out_of_context_variations)

    # 8. RESPONS DEFAULT SANTAI
    default_variations = [
        "Halo Kak! Aku Leli, asisten AI budidaya ikan lele. 😊\n\n"
        "Ada yang bisa Leli bantu untuk kolam lele Kakak hari ini? Kakak bisa tanya soal:\n"
        "• **Penyakit lele** (seperti Malnutrisi, Jamur, Overfeeding, atau Aeromonas)\n"
        "• **Manajemen Air & Pakan**\n"
        "• **Cara Tebar Bibit & Panen**\n\n",
        
        "Hai Kak! Leli di sini untuk membantu Anda mengelola peternakan lele. 🐟✨\n\n"
        "Silakan ajukan pertanyaan seputar:\n"
        "• Berapa porsi pakan yang tepat?\n"
        "• Cara mengobati jamur air?\n"
        "• Prosedur fermentasi EM4?\n"
        "Tuliskan pertanyaan Kakak di bawah ya!"
    ]
    return random.choice(default_variations)


# --------------------------------------------------------------------------- #
#  System Prompt & Main Function
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """Kamu adalah 'Leli', asisten AI ahli budidaya ikan lele untuk platform Ternak Lele.
Tugas kamu:
- Menjawab pertanyaan seputar budidaya lele, penyakit, obat-obatan, dan manajemen kolam
- Menggunakan bahasa Indonesia yang mudah dipahami petani
- Memberikan saran praktis berbasis ilmiah
- Merujuk ke pakar perikanan untuk kasus yang kompleks

Jika ada konteks pengetahuan di bawah ini, jadikan referensi utama dalam menjawab."""


def get_ai_response(user_message: str, history: list = None) -> str:
    """
    Generate respons AI dengan RAG context.

    Args:
        user_message: Pesan dari pengguna.
        history: List dict [{"role": "user"|"ai", "content": str}]

    Returns:
        String respons dari AI.
    """
    # Ambil konteks knowledge dulu (selalu diperlukan)
    context = get_knowledge_context(user_message)

    # Coba gunakan OpenAI jika API key tersedia
    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import SystemMessage, HumanMessage, AIMessage

            system_content = SYSTEM_PROMPT
            if context:
                system_content += f"\n\nKonteks Pengetahuan:\n{context}"

            messages = [SystemMessage(content=system_content)]

            # Tambahkan riwayat percakapan (max 6 pesan terakhir)
            if history:
                for msg in history[-6:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))

            messages.append(HumanMessage(content=user_message))

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=800,
                api_key=settings.OPENAI_API_KEY,
                timeout=2.0,  # Batasi timeout 2 detik agar tidak membekukan server saat offline
            )

            response = llm.invoke(messages)
            return response.content

        except ImportError:
            logger.warning("LangChain tidak tersedia, menggunakan offline responder.")
        except Exception as e:
            logger.error(f"Error AI response (OpenAI): {e}")

    # Fallback: Smart offline responder
    return _build_smart_response(user_message, context)
