/**
 * Standalone Client-Side Application Logic untuk Ternak Lele Web SPA
 * Versi Serverless / Static Web yang menggunakan local simulation untuk AI, Chatbot, dan Auth
 */

// Mock Databases
const DISEASES_DB = [
    {
        nama: "Aeromonas",
        nama_ilmiah: "Aeromonas hydrophila",
        deskripsi: "Penyakit bakterial paling umum pada lele, disebabkan bakteri gram-negatif Aeromonas hydrophila. Sangat menular dan dapat menyebabkan kematian massal.",
        gejala: "Luka borok kemerahan pada kulit, perut kembung berisi cairan, sirip geripis, nafsu makan menurun, gerakan lemah dan berenang tidak normal, insang pucat.",
        penyebab: "Bakteri Aeromonas hydrophila yang berkembang pesat pada kualitas air buruk, kepadatan tinggi, suhu air tidak stabil, dan stres akibat transportasi.",
        pencegahan: "Jaga kualitas air (pH 6.5-8, DO >5 mg/L, suhu 26-30°C). Kurangi kepadatan tebar. Desinfeksi kolam sebelum tebar. Pemberian probiotik rutin.",
        penanganan: "Isolasi ikan sakit segera. Rendam dalam larutan garam NaCl 3-5% selama 5-10 menit. Pengobatan dengan antibiotik Oksitetrasiklin 50-75 mg/kg pakan selama 7-10 hari. Tambahkan vitamin C ke pakan untuk meningkatkan imunitas.",
        obat_list: [
            {nama_obat: "Oksitetrasiklin", dosis: "50-75 mg/kg pakan/hari", cara_penggunaan: "Campurkan ke dalam pakan, berikan 2x sehari selama 7-10 hari.", catatan: "Hentikan 2 minggu sebelum panen."},
            {nama_obat: "Garam NaCl", dosis: "30-50 gram per liter air", cara_penggunaan: "Larutkan dalam air, rendam ikan selama 5-10 menit, ulangi 2-3 hari.", catatan: "Untuk penanganan awal dan desinfeksi ringan."}
        ]
    },
    {
        nama: "Malnutrisi",
        nama_ilmiah: "Defisiensi Nutrisi Kronis",
        deskripsi: "Kondisi kekurangan gizi kronis pada lele yang ditandai dengan kepala berukuran besar tidak proporsional dibanding badan yang kecil dan kurus. Terjadi akibat pakan tidak mencukupi kebutuhan nutrisi ikan.",
        gejala: "Kepala tampak besar dan tidak proporsional dengan tubuh yang sangat kecil/kurus, tulang belakang terlihat menonjol, perut cekung, warna tubuh pucat, pertumbuhan sangat terhambat, ikan lamban dan mudah stres.",
        penyebab: "Kekurangan pakan secara konsisten, kualitas pakan rendah (protein tidak mencukupi), persaingan pakan yang ketat akibat kepadatan tinggi, atau ikan lemah yang kalah bersaing mendapatkan pakan.",
        pencegahan: "Lakukan grading/sortasi ukuran ikan secara rutin. Berikan pakan sesuai kebutuhan (3-5% biomassa/hari). Gunakan pakan berkualitas dengan protein minimal 30%. Pastikan semua ikan mendapat jatah pakan yang sama.",
        penanganan: "Tingkatkan frekuensi pemberian pakan 3-4 kali sehari. Gunakan pakan dengan kandungan protein tinggi (30-35%). Pisahkan ikan kecil dari yang besar agar dapat pakan merata. Tambahkan suplemen vitamin dan mineral ke pakan.",
        obat_list: [
            {nama_obat: "Vitamin C (Asam Askorbat)", dosis: "100-200 mg/kg pakan", cara_penggunaan: "Campurkan ke pakan setiap hari untuk meningkatkan imunitas dan pemulihan.", catatan: "Aman digunakan hingga panen."},
            {nama_obat: "Suplemen Mineral Perikanan", dosis: "2-3 g/kg pakan", cara_penggunaan: "Campurkan ke pakan 3x seminggu selama masa pemulihan.", catatan: "Tersedia di toko pertanian/perikanan."}
        ]
    },
    {
        nama: "Jamur",
        nama_ilmiah: "Saprolegnia sp. / Achlya sp.",
        deskripsi: "Infeksi jamur (mikosis) pada lele, umumnya sebagai infeksi sekunder setelah luka bakterial. Ditandai pertumbuhan benang putih seperti kapas.",
        gejala: "Pertumbuhan benang putih/abu-abu seperti kapas pada kulit, insang, atau telur. Ikan lemah, malas bergerak, nafsu makan turun. Luka di bawah hifa terlihat kemerahan.",
        penyebab: "Jamur air Saprolegnia berkembang pada air dingin (<22°C), kualitas air buruk, bahan organik tinggi, dan ikan yang sudah lemah atau terluka.",
        pencegahan: "Jaga suhu air di atas 26°C. Kurangi bahan organik di dasar kolam. Tidak overfeeding. Desinfeksi telur dengan Malachite Green sebelum penetasan.",
        penanganan: "Naikkan suhu air ke 28-30°C. Rendam dengan larutan Malachite Green Oxalate 0.1 ppm selama 1 jam atau Methylene Blue 1-2 ppm. Ganti 50% air kolam. Tingkatkan aerasi.",
        obat_list: [
            {nama_obat: "Methylene Blue", dosis: "1-2 mg/L (ppm)", cara_penggunaan: "Larutkan dalam air kolam, diamkan 24 jam, lalu ganti sebagian air.", catatan: "Aman untuk benih, hindari cahaya matahari langsung."},
            {nama_obat: "Kalium Permanganat (KMnO4)", dosis: "2-4 mg/L", cara_penggunaan: "Larutkan dan rendam selama 30-60 menit, bilas dengan air bersih.", catatan: "Hati-hati overdosis, dapat mematikan ikan."}
        ]
    },
    {
        nama: "Overfeeding",
        nama_ilmiah: "Gangguan Pencernaan / Digestive Disorder",
        deskripsi: "Gangguan pencernaan akibat pemberian pakan berlebih (overfeeding) yang menyebabkan perut lele membuncit, terapung, dan tidak bisa berenang normal. Kondisi ini bisa mematikan jika tidak segera ditangani.",
        gejala: "Perut sangat membuncit dan keras, ikan terapung atau berenang miring di permukaan, gerakan lamban dan tidak berkoordinasi, tidak mau makan, buang kotoran berlebihan atau tidak keluar, warna feses tidak normal (putih atau sangat gelap).",
        penyebab: "Pemberian pakan melebihi kapasitas lambung ikan, pemberian pakan tidak terjadwal, pakan yang mengembang di dalam perut (pakan kering tanpa direndam), atau pakan yang sudah rusak/berjamur.",
        pencegahan: "Atur jadwal pakan yang ketat (2-3x sehari). Berikan pakan secukupnya, amati sampai ikan berhenti makan aktif (±15 menit). Rendam pakan kering sebelum diberikan. Kurangi pakan saat cuaca panas atau hujan lebat.",
        penanganan: "Hentikan pemberian pakan selama 1-2 hari. Ganti 30-40% air kolam dengan air segar. Tambahkan probiotik ke air kolam. Berikan daun pepaya atau bawang putih yang dicincang ke dalam air sebagai stimulan pencernaan alami.",
        obat_list: [
            {nama_obat: "Probiotik Perikanan", dosis: "1-2 g/100L air kolam", cara_penggunaan: "Larutkan dalam air, tuangkan ke kolam, ulangi 2-3 hari.", catatan: "Bantu pemulihan bakteri pencernaan alami."},
            {nama_obat: "Bawang Putih Cincang", dosis: "5 gram/kg pakan atau 10 gram per 100L air", cara_penggunaan: "Larutkan ekstrak di air kolam, biarkan 24 jam.", catatan: "Stimulan pencernaan alami yang aman."}
        ]
    },
    {
        nama: "Sehat",
        nama_ilmiah: "-",
        deskripsi: "Kondisi ikan lele yang sehat dan normal tanpa indikasi penyakit.",
        gejala: "Tidak ada gejala penyakit. Ikan aktif, nafsu makan baik, warna tubuh normal, insang merah segar, tidak ada luka atau pertumbuhan abnormal.",
        penyebab: "Tidak berlaku (kondisi normal).",
        pencegahan: "Manajemen kolam baik: ganti air rutin 20-30% per minggu, probiotik, vitamin C, jaga pH 6.5-8, suhu 26-30°C, DO >5 mg/L.",
        penanganan: "Pertahankan kualitas air optimal, berikan pakan bergizi seimbang, jaga kepadatan tebar, lakukan monitoring rutin.",
        obat_list: []
    }
];

const ARTICLES_DB = [
    {
        judul: "Manajemen Kualitas Air untuk Budidaya Lele Optimal",
        kategori: "Manajemen Kolam",
        konten: `Kualitas air adalah faktor paling kritis dalam budidaya lele. Parameter yang harus dijaga secara rutin:\n\n**pH Air**\nLele tumbuh optimal pada pH 6.5-8.0. pH di bawah 6 atau di atas 9 dapat menyebabkan stres dan rentan penyakit. Gunakan kapur dolomit untuk menaikkan pH dan tawas untuk menurunkan.\n\n**Oksigen Terlarut (DO)**\nMinimal 4-5 mg/L. Tambahkan aerator jika DO turun. Tanda DO rendah: ikan naik ke permukaan dan megap-megap di pagi hari.\n\n**Suhu**\nSuhu optimal 26-30°C. Di bawah 22°C pertumbuhan melambat dan rentan jamur. Di atas 32°C ikan stres dan nafsu makan turun.\n\n**Amonia (NH3)**\nHarus di bawah 0.02 mg/L. Amonia tinggi dari kotoran ikan dan sisa pakan menyebabkan keracunan. Solusi: ganti air rutin, kurangi pakan, tambahkan probiotik.\n\n**Penggantian Air**\nGanti 20-30% volume air setiap minggu. Saat musim panas atau kepadatan tinggi, ganti lebih sering. Air baru sebaiknya diendapkan dulu 24 jam.`
    },
    {
        judul: "Panduan Pemberian Pakan Lele yang Efektif dan Efisien",
        kategori: "Nutrisi & Pakan",
        konten: `Pakan merupakan 60-70% dari total biaya operasional budidaya lele. Manajemen pakan yang tepat menentukan FCR (Feed Conversion Ratio) yang efisien.\n\n**Frekuensi Pemberian Pakan**\nBenih (<5 cm): 4-5 kali sehari\nFingerling (5-10 cm): 3-4 kali sehari\nLele konsumsi (>10 cm): 2-3 kali sehari\n\n**Jumlah Pakan**\nBerikan pakan 3-5% dari biomassa total per hari. Evaluasi setiap 2 minggu dengan sampling berat ikan.\n\n**Waktu Pemberian**\nHindari pemberian pakan tengah hari saat suhu paling tinggi. Optimal: pagi (06.00-07.00), sore (17.00-18.00), malam (21.00-22.00).\n\n**Tanda Pakan Cukup**\nIkan masih aktif makan setelah 15-20 menit. Jika ada sisa pakan, kurangi jumlahnya karena sisa pakan meningkatkan amonia.\n\n**Bahaya Overfeeding**\nPemberian pakan berlebih menyebabkan gangguan pencernaan (perut kembung) dan pencemaran air. Selalu amati respons ikan saat diberi pakan.\n\n**Suplemen**\nVitamin C 100-200 mg/kg pakan meningkatkan imunitas. Probiotik 1-2 g/kg pakan memperbaiki pencernaan dan kualitas air.`
    },
    {
        judul: "Cara Mencegah dan Mengatasi Penyakit Aeromonas pada Lele",
        kategori: "Pengendalian Penyakit",
        konten: `Aeromonas hydrophila adalah musuh utama pembudidaya lele. Penyakit ini bisa meludeskan seluruh kolam dalam hitungan hari jika tidak ditangani cepat.\n\n**Deteksi Awal**\nPerhatikan tanda-tanda: ikan berenang di permukaan, nafsu makan turun tiba-tiba, muncul luka kemerahan di tubuh. Segera isolasi ikan yang tampak sakit.\n\n**Penanganan Darurat**\n1. Isolasi ikan sakit ke wadah terpisah\n2. Ganti 50% air kolam dengan air segar yang sudah diendapkan\n3. Tambahkan garam NaCl 500 gram per 100 liter air (5 g/L)\n4. Tingkatkan aerasi maksimal\n\n**Pengobatan Medis**\nOksitetrasiklin (OTC) 50 mg/kg pakan selama 7-10 hari adalah pilihan umum. Jangan gunakan antibiotik sembarangan karena dapat menimbulkan resistensi.\n\n**Pencegahan Jangka Panjang**\n- Probiotik Bacillus sp. 1-2 g/kg pakan 3x seminggu\n- Bawang putih cincang 5 g/kg pakan sebagai antibakteri alami\n- Desinfeksi kolam sebelum tebar`
    },
    {
        judul: "Mengenali dan Menangani Malnutrisi pada Lele: Kepala Besar Badan Kecil",
        kategori: "Pengendalian Penyakit",
        konten: `Malnutrisi atau kekurangan gizi adalah masalah yang sering luput dari perhatian pembudidaya, namun bisa menyebabkan kerugian besar akibat pertumbuhan yang tidak seragam.\n\n**Tanda-Tanda Malnutrisi**\nKepala besar yang tidak proporsional dibanding badan, ikan sangat kurus, dan gerakan lamban.\n\n**Solusi Penanganan**\nGrading ukuran secara berkala agar tidak kalah bersaing pakan. Berikan pelet protein >30% yang dibasahi vitamin C/suplemen perikanan.`
    }
];

const CHATBOT_KEYWORDS = {
    intro: ["siapa kamu", "siapa leli", "kenalan", "nama kamu", "kamu siapa", "leli itu siapa", "leli siapa"],
    greeting: ["halo", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "assalamualaikum", "p", "permisi", "apa kabar"],
    pakan: ["pakan", "makan", "feed", "nutrisi", "protein", "dosis pakan"],
    air: ["air", "ph", "oksigen", "kualitas air", "ganti air", "bersih", "amonia"],
    kolam: ["kolam", "terpal", "beton", "tanah", "persiapan", "luas"],
    bibit: ["bibit", "benih", "anakan", "tebar", "padat tebar"],
    panen: ["panen", "ukuran", "bobot", "waktu panen", "konsumsi"],
    probiotik: ["probiotik", "em4", "bakteri baik", "fermentasi"],
    garam: ["garam", "natrium", "sodium", "krosok"],
    kanibal: ["kanibal", "saling makan", "grading", "sortasi", "kepadatan", "ukuran beda"],
    biaya: ["biaya", "modal", "untung", "fcr", "keuntungan", "harga", "pasar"],
    aeromonas: ["aeromonas", "borok", "luka", "bakteri", "bercak", "merah"],
    malnutrisi: ["malnutrisi", "gizi", "kepala besar", "kurus", "badan kecil"],
    jamur: ["jamur", "kapas", "putih", "saprolegnia", "fungi"],
    overfeeding: ["overfeeding", "kembung", "pencernaan", "pakan berlebih", "terapung", "perut besar"],
    sehat: ["sehat", "normal", "baik", "segar"],
    outOfContext: ["siapa presiden", "cuaca", "berita", "politik", "rendang", "masak", "sejarah", "games", "game", "main", "lagu", "musik", "film", "saham", "crypto", "belanja", "harga", "uang", "pacar", "cinta"]
};

// Application State
const state = {
    token: localStorage.getItem("lele_static_token") || null,
    user: JSON.parse(localStorage.getItem("lele_static_user")) || null,
    diseases: DISEASES_DB,
    articles: ARTICLES_DB,
    activeSessionId: null,
    selectedFile: null,
    history: JSON.parse(localStorage.getItem("lele_static_history")) || [],
    chatSessions: JSON.parse(localStorage.getItem("lele_static_chat_sessions")) || []
};

// Initializer
document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    setupNavigation();
    setupAuthForms();
    setupUpload();
    setupChat();
    setupToasts();
    
    // Check initial auth status
    if (state.token && state.user) {
        loginUserSession(state.user, state.token);
    } else {
        showSection("landing");
        updateSidebarUI(false);
    }
    
    // Load public data
    displayDiseases(state.diseases);
    displayArticles(state.articles);
}

/* ─────────────────────────────────────────────────────────────────────────
   TOAST NOTIFICATION SYSTEM
   ───────────────────────────────────────────────────────────────────────── */
let toastContainer;
function setupToasts() {
    toastContainer = document.createElement("div");
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);
}

function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerText = message;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = "slideIn 0.3s cubic-bezier(0.1, 0.8, 0.2, 1) reverse";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ─────────────────────────────────────────────────────────────────────────
   ROUTING & NAVIGATION (SPA)
   ───────────────────────────────────────────────────────────────────────── */
function setupNavigation() {
    const navLinks = document.querySelectorAll(".nav-item a, .nav-action");
    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const targetSection = link.getAttribute("data-section");
            
            // Protect authenticated sections
            const authRequired = ["dashboard", "detection", "chatbot", "history"].includes(targetSection);
            if (authRequired && !state.token) {
                showToast("Anda harus masuk terlebih dahulu.", "error");
                showSection("auth");
                return;
            }
            
            showSection(targetSection);
        });
    });
    
    // Logout Handler
    document.querySelector(".logout-btn").addEventListener("click", () => {
        logout();
    });
}

function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll(".app-section");
    sections.forEach(sec => sec.classList.remove("active"));
    
    // Show target section
    const targetSection = document.getElementById(`section-${sectionId}`);
    if (targetSection) {
        targetSection.classList.add("active");
        
        // Custom actions when entering section
        if (sectionId === "dashboard") {
            loadDashboardData();
        } else if (sectionId === "history") {
            loadDetectionHistory();
        } else if (sectionId === "chatbot") {
            loadChatSessions();
        }
    }
    
    // Update active nav-item class in sidebar
    const navItems = document.querySelectorAll(".nav-links .nav-item");
    navItems.forEach(item => item.classList.remove("active"));
    
    const activeNavItem = document.getElementById(`nav-${sectionId}-item`);
    if (activeNavItem) {
        activeNavItem.classList.add("active");
    }
}

function updateSidebarUI(isAuthenticated) {
    const navDashboard = document.getElementById("nav-dashboard-item");
    const navHistory = document.getElementById("nav-history-item");
    const navLogin = document.getElementById("nav-login-item");
    const profileWidget = document.querySelector(".user-profile-widget");
    
    if (isAuthenticated) {
        navDashboard.style.display = "block";
        navHistory.style.display = "block";
        navLogin.style.display = "none";
        profileWidget.style.display = "flex";
        
        // Fill profile details
        if (state.user) {
            document.querySelector(".user-name").innerText = state.user.name || state.user.username;
            document.querySelector(".user-role").innerText = state.user.is_pakar ? "Pakar Perikanan" : "Pembudidaya Lele";
            document.querySelector(".user-avatar").innerText = (state.user.name || state.user.username).substring(0, 2).toUpperCase();
        }
    } else {
        navDashboard.style.display = "none";
        navHistory.style.display = "none";
        navLogin.style.display = "block";
        profileWidget.style.display = "none";
    }
}

/* ─────────────────────────────────────────────────────────────────────────
   AUTHENTICATION SIMULATION
   ───────────────────────────────────────────────────────────────────────── */
function setupAuthForms() {
    const loginForm = document.getElementById("form-login");
    const registerForm = document.getElementById("form-register");
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    
    tabRegister.addEventListener("click", (e) => {
        e.preventDefault();
        loginForm.style.display = "none";
        registerForm.style.display = "block";
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
    });
    
    tabLogin.addEventListener("click", (e) => {
        e.preventDefault();
        registerForm.style.display = "none";
        loginForm.style.display = "block";
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
    });
    
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;
        
        if (!username || !password) {
            showToast("Harap isi semua kolom.", "error");
            return;
        }
        
        // Successful login
        const mockUser = {
            username: username,
            name: username.charAt(0).toUpperCase() + username.slice(1),
            email: `${username}@gmail.com`,
            is_pakar: username.toLowerCase().includes("pakar")
        };
        const mockToken = "mock_jwt_token_" + Math.random().toString(36).substring(7);
        
        loginUserSession(mockUser, mockToken);
        showToast(`Selamat datang kembali, ${mockUser.name}!`, "success");
        showSection("dashboard");
    });
    
    registerForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const username = document.getElementById("reg-username").value.trim();
        const email = document.getElementById("reg-email").value.trim();
        const password = document.getElementById("reg-password").value;
        
        if (!username || !email || !password) {
            showToast("Semua kolom harus diisi.", "error");
            return;
        }
        
        const mockUser = {
            username: username,
            name: username.charAt(0).toUpperCase() + username.slice(1),
            email: email,
            is_pakar: username.toLowerCase().includes("pakar")
        };
        const mockToken = "mock_jwt_token_" + Math.random().toString(36).substring(7);
        
        loginUserSession(mockUser, mockToken);
        showToast("Registrasi akun berhasil!", "success");
        showSection("dashboard");
    });
}

function loginUserSession(user, token) {
    state.token = token;
    state.user = user;
    localStorage.setItem("lele_static_token", token);
    localStorage.setItem("lele_static_user", JSON.stringify(user));
    
    updateSidebarUI(true);
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("lele_static_token");
    localStorage.removeItem("lele_static_user");
    
    updateSidebarUI(false);
    showToast("Anda telah keluar dari aplikasi.", "info");
    showSection("landing");
}

/* ─────────────────────────────────────────────────────────────────────────
   DASHBOARD SIMULATION
   ───────────────────────────────────────────────────────────────────────── */
function loadDashboardData() {
    // Update welcome name
    const welcomeEl = document.getElementById("welcome-name");
    if (welcomeEl && state.user) {
        welcomeEl.innerText = state.user.name || state.user.username;
    }
    
    // Total Detections
    const statTotal = document.getElementById("stat-total");
    if (statTotal) statTotal.innerText = state.history.length;
    
    // Healthy count vs sick
    const sehatCount = state.history.filter(h => h.penyakit_terdeteksi === "Sehat").length;
    const sakitCount = state.history.length - sehatCount;
    
    const statSehat = document.getElementById("stat-sehat");
    if (statSehat) statSehat.innerText = sehatCount;
    
    const statSakit = document.getElementById("stat-sakit");
    if (statSakit) statSakit.innerText = sakitCount;
}

/* ─────────────────────────────────────────────────────────────────────────
   AI CAMERA & DETECTION SIMULATION (OFFLINE MOCK CLASSIFIER)
   ───────────────────────────────────────────────────────────────────────── */
function setupUpload() {
    const dragArea = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("file-input");
    const previewContainer = document.querySelector(".preview-container");
    const previewImg = document.querySelector(".preview-img");
    const btnSubmit = document.getElementById("btn-analyze-ai");
    const resultContainer = document.querySelector(".result-container");
    
    // Drag and Drop
    dragArea.addEventListener("click", () => fileInput.click());
    
    dragArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        dragArea.style.borderColor = "var(--primary)";
        dragArea.style.background = "rgba(59, 130, 246, 0.08)";
    });
    
    dragArea.addEventListener("dragleave", () => {
        dragArea.style.borderColor = "rgba(255, 255, 255, 0.15)";
        dragArea.style.background = "rgba(255, 255, 255, 0.03)";
    });
    
    dragArea.addEventListener("drop", (e) => {
        e.preventDefault();
        dragArea.style.borderColor = "rgba(255, 255, 255, 0.15)";
        dragArea.style.background = "rgba(255, 255, 255, 0.03)";
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener("change", (e) => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });
    
    function handleFileSelect(file) {
        if (file.size > 10 * 1024 * 1024) {
            showToast("File tidak boleh lebih besar dari 10MB.", "error");
            return;
        }
        
        state.selectedFile = file;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewContainer.style.display = "block";
            btnSubmit.style.display = "inline-flex";
            resultContainer.style.display = "none";
        };
        reader.readAsDataURL(file);
    }
    
    btnSubmit.addEventListener("click", () => {
        if (!state.selectedFile) return;
        
        // Loader
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<div class="loader-spinner" style="width:20px;height:20px;margin:0;"></div> Memproses...`;
        
        // Simulate local AI Classification delay (1.5 seconds)
        setTimeout(() => {
            runMockClassifier();
        }, 1500);
    });
}

function resetAnalyzeButton() {
    const btnSubmit = document.getElementById("btn-analyze-ai");
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = `🐟 Mulai Analisis AI`;
}

function runMockClassifier() {
    const fileName = state.selectedFile.name.toLowerCase();
    
    // Choose disease based on file name keywords, else pick random
    let diseaseName = "Sehat";
    if (fileName.includes("aeromonas") || fileName.includes("borok") || fileName.includes("merah")) {
        diseaseName = "Aeromonas";
    } else if (fileName.includes("jamur") || fileName.includes("kapas") || fileName.includes("putih")) {
        diseaseName = "Jamur";
    } else if (fileName.includes("malnutrisi") || fileName.includes("kurus") || fileName.includes("kepala")) {
        diseaseName = "Malnutrisi";
    } else if (fileName.includes("overfeeding") || fileName.includes("kembung") || fileName.includes("buncit")) {
        diseaseName = "Overfeeding";
    } else {
        // Random disease selection for demo
        const diseases = ["Sehat", "Aeromonas", "Malnutrisi", "Jamur", "Overfeeding"];
        diseaseName = diseases[Math.floor(Math.random() * diseases.length)];
    }
    
    // Generate scores
    const confidence = parseFloat((0.82 + Math.random() * 0.17).toFixed(4));
    
    // Generate probabilities
    const probs = {};
    let sum = 0;
    const classes = ["Sehat", "Aeromonas", "Malnutrisi", "Jamur", "Overfeeding"];
    
    classes.forEach(c => {
        if (c === diseaseName) {
            probs[c] = confidence;
        } else {
            probs[c] = parseFloat((Math.random() * (1 - confidence) / 4).toFixed(4));
        }
        sum += probs[c];
    });
    
    // Adjust remainder so sum is exactly 1.0
    const diff = 1.0 - sum;
    const randomClass = classes[Math.floor(Math.random() * classes.length)];
    probs[randomClass] = parseFloat((probs[randomClass] + diff).toFixed(4));
    
    // Retrieve treatment recommendation
    const diseaseData = DISEASES_DB.find(d => d.nama === diseaseName);
    const penanganan = diseaseData ? diseaseData.penanganan : "Konsultasikan dengan pakar perikanan.";
    
    const newLog = {
        id: state.history.length + 1,
        created_at: new Date().toISOString(),
        penyakit_terdeteksi: diseaseName,
        confidence_score: confidence,
        confidence_persen: `${Math.round(confidence * 100)}%`,
        semua_probabilitas: probs,
        rekomendasi_penanganan: penanganan,
        status_proses: "done",
        image: document.querySelector(".preview-img").src
    };
    
    // Save to State & LocalStorage
    state.history.push(newLog);
    localStorage.setItem("lele_static_history", JSON.stringify(state.history));
    
    showToast("Analisis AI selesai!", "success");
    displayDetectionResult(newLog);
    resetAnalyzeButton();
}

function displayDetectionResult(result) {
    const resultContainer = document.querySelector(".result-container");
    resultContainer.style.display = "block";
    
    // Label & Badge
    const labelEl = document.getElementById("res-label");
    const badgeEl = document.getElementById("res-badge");
    const deskripsiEl = document.getElementById("res-desc");
    const penangananEl = document.getElementById("res-treatment");
    
    const penyakitNama = result.penyakit_terdeteksi;
    labelEl.innerText = penyakitNama.replace("_", " ");
    
    if (penyakitNama === "Sehat") {
        badgeEl.innerText = "Sehat";
        badgeEl.className = "result-badge badge-sehat";
        deskripsiEl.innerText = "Selamat! Ikan lele Anda terdeteksi sehat dan normal.";
    } else {
        badgeEl.innerText = "Sakit";
        badgeEl.className = "result-badge badge-sakit";
        deskripsiEl.innerText = `Ikan lele Anda terindikasi terkena penyakit ${penyakitNama.replace("_", " ")}.`;
    }
    
    // Confidence Score
    const scoreVal = result.confidence_score !== null ? result.confidence_score : 0;
    const scorePercent = Math.round(scoreVal * 100);
    document.getElementById("res-score-text").innerText = `${scorePercent}%`;
    
    // Radial Progress animation
    const ringBar = document.querySelector(".progress-ring-bar");
    const offset = 345.5 - (scoreVal * 345.5);
    ringBar.style.strokeDashoffset = offset;
    
    // Probabilities Bar chart
    const probList = document.getElementById("res-probabilities");
    probList.innerHTML = "";
    
    const probs = result.semua_probabilitas || {};
    const labels = Object.keys(probs);
    
    labels.forEach(lbl => {
        const value = probs[lbl] || 0;
        const pct = Math.round(value * 100);
        
        const item = document.createElement("div");
        item.className = "prob-item";
        item.innerHTML = `
            <div class="prob-info">
                <span>${lbl.replace("_", " ")}</span>
                <span>${pct}%</span>
            </div>
            <div class="prob-track">
                <div class="prob-bar" style="width: 0%"></div>
            </div>
        `;
        probList.appendChild(item);
        
        // Trigger width animation
        setTimeout(() => {
            const bar = item.querySelector(".prob-bar");
            if (bar) bar.style.width = `${pct}%`;
        }, 100);
    });
    
    // Penanganan
    penangananEl.innerHTML = result.rekomendasi_penanganan || "Tidak ada rekomendasi spesifik.";
    
    // Chat button shortcut
    const chatBtn = document.getElementById("btn-chat-shortcut");
    chatBtn.onclick = () => {
        startChatAbout(penyakitNama);
    };
    
    // Scroll to results
    resultContainer.scrollIntoView({ behavior: "smooth" });
}

function startChatAbout(diseaseName) {
    state.isStartingChatAbout = true;
    showSection("chatbot");
    startNewChatSession();
    const messageInput = document.getElementById("chat-message-input");
    if (diseaseName === "Sehat") {
        messageInput.value = "Halo Leli, bagaimanakah cara menjaga kualitas air kolam lele agar ikan tetap sehat?";
    } else {
        messageInput.value = `Halo Leli, ikan lele saya baru saja didiagnosis terkena penyakit ${diseaseName.replace("_", " ")}. Bagaimana penanganan darurat yang bisa saya lakukan?`;
    }
    messageInput.focus();
    sendMessage();
    state.isStartingChatAbout = false;
}

/* ─────────────────────────────────────────────────────────────────────────
   CHATBOT LOGIC (LELI MOCK OFFLINE RESPONDER)
   ───────────────────────────────────────────────────────────────────────── */
function setupChat() {
    const btnNewSession = document.getElementById("btn-new-session");
    const messageInput = document.getElementById("chat-message-input");
    const btnSend = document.getElementById("btn-send-message");
    
    btnNewSession.addEventListener("click", () => {
        startNewChatSession();
    });
    
    btnSend.addEventListener("click", () => {
        sendMessage();
    });
    
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function loadChatSessions() {
    const listContainer = document.getElementById("chat-sessions-list");
    listContainer.innerHTML = "";
    
    if (state.chatSessions.length === 0) {
        listContainer.innerHTML = `<p style="font-size: 13px; color: var(--text-muted); text-align: center; margin-top:20px;">Belum ada sesi percakapan.</p>`;
        startNewChatSession(); // Auto-create first session
        return;
    }
    
    state.chatSessions.forEach(session => {
        const item = document.createElement("div");
        item.className = `session-item ${session.id === state.activeSessionId ? "active" : ""}`;
        item.innerHTML = `
            <div class="session-summary">${session.context_summary || "Sesi Baru"}</div>
            <div class="session-date">${new Date(session.updated_at).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "short" })}</div>
        `;
        item.addEventListener("click", () => {
            openChatSession(session.id);
        });
        listContainer.appendChild(item);
    });
    
    // Open first session if none is active
    if (!state.activeSessionId && state.chatSessions.length > 0 && !state.isStartingChatAbout) {
        openChatSession(state.chatSessions[0].id);
    }
}

function startNewChatSession() {
    // Generate new mock session
    const newSessionId = state.chatSessions.length + 1;
    const newSession = {
        id: newSessionId,
        context_summary: "Sesi Baru",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: []
    };
    
    state.chatSessions.push(newSession);
    localStorage.setItem("lele_static_chat_sessions", JSON.stringify(state.chatSessions));
    
    state.activeSessionId = newSessionId;
    
    // Clear chat bubbles & load initial Leli bubble
    const messagesEl = document.getElementById("chat-messages-container");
    messagesEl.innerHTML = `
        <div class="chat-bubble chat-bubble-ai">
            Halo! Saya Leli, asisten virtual budidaya ikan lele Anda. Ada yang bisa saya bantu hari ini seputar kesehatan kolam, nutrisi pakan, atau penyakit lele Anda? 😊
            <div class="chat-bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
    
    loadChatSessionsListOnly();
}

function openChatSession(sessionId) {
    state.activeSessionId = sessionId;
    
    // Highlight item
    document.querySelectorAll(".session-item").forEach(item => {
        item.classList.remove("active");
    });
    
    const session = state.chatSessions.find(s => s.id === sessionId);
    const messagesEl = document.getElementById("chat-messages-container");
    messagesEl.innerHTML = "";
    
    if (!session || session.messages.length === 0) {
        messagesEl.innerHTML = `
            <div class="chat-bubble chat-bubble-ai">
                Halo! Saya Leli, asisten virtual budidaya ikan lele Anda. Ada yang bisa saya bantu hari ini? 😊
                <div class="chat-bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            </div>
        `;
    } else {
        session.messages.forEach(msg => {
            const bubble = document.createElement("div");
            bubble.className = `chat-bubble chat-bubble-${msg.sender_type === "user" ? "user" : "ai"}`;
            const formattedText = msg.message_text.replace(/\n/g, "<br>");
            bubble.innerHTML = `
                ${formattedText}
                <div class="chat-bubble-time">${new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            `;
            messagesEl.appendChild(bubble);
        });
    }
    
    scrollChatToBottom();
    loadChatSessionsListOnly();
}

function loadChatSessionsListOnly() {
    const listContainer = document.getElementById("chat-sessions-list");
    listContainer.innerHTML = "";
    
    state.chatSessions.forEach(session => {
        const item = document.createElement("div");
        item.className = `session-item ${session.id === state.activeSessionId ? "active" : ""}`;
        item.innerHTML = `
            <div class="session-summary">${session.context_summary || "Sesi Baru"}</div>
            <div class="session-date">${new Date(session.updated_at).toLocaleString("id-ID", { dateStyle: "short", timeStyle: "short" })}</div>
        `;
        item.addEventListener("click", () => {
            openChatSession(session.id);
        });
        listContainer.appendChild(item);
    });
}

function sendMessage() {
    const messageInput = document.getElementById("chat-message-input");
    const message = messageInput.value.trim();
    if (!message) return;
    
    messageInput.value = "";
    
    // Add user bubble instantly
    const messagesEl = document.getElementById("chat-messages-container");
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble chat-bubble-user";
    userBubble.innerHTML = `
        ${message}
        <div class="chat-bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
    `;
    messagesEl.appendChild(userBubble);
    scrollChatToBottom();
    
    // Save user message to storage
    const sessionIndex = state.chatSessions.findIndex(s => s.id === state.activeSessionId);
    if (sessionIndex !== -1) {
        state.chatSessions[sessionIndex].messages.push({
            sender_type: "user",
            message_text: message,
            created_at: new Date().toISOString()
        });
        state.chatSessions[sessionIndex].context_summary = message.substring(0, 50) + (message.length > 50 ? "..." : "");
        state.chatSessions[sessionIndex].updated_at = new Date().toISOString();
        localStorage.setItem("lele_static_chat_sessions", JSON.stringify(state.chatSessions));
        loadChatSessionsListOnly();
    }
    
    // Add typing indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "chat-bubble chat-bubble-ai typing-indicator-bubble";
    typingIndicator.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    messagesEl.appendChild(typingIndicator);
    scrollChatToBottom();
    
    // Simulate Leli responding after 1.2s
    setTimeout(() => {
        typingIndicator.remove();
        const responseText = getSimulatedLeliResponse(message);
        
        const aiBubble = document.createElement("div");
        aiBubble.className = "chat-bubble chat-bubble-ai";
        const formattedResponse = responseText.replace(/\n/g, "<br>");
        aiBubble.innerHTML = `
            ${formattedResponse}
            <div class="chat-bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        `;
        messagesEl.appendChild(aiBubble);
        scrollChatToBottom();
        
        // Save Leli message to storage
        if (sessionIndex !== -1) {
            state.chatSessions[sessionIndex].messages.push({
                sender_type: "ai",
                message_text: responseText,
                created_at: new Date().toISOString()
            });
            localStorage.setItem("lele_static_chat_sessions", JSON.stringify(state.chatSessions));
        }
    }, 1200);
}

function getSimulatedLeliResponse(query) {
    const q_lower = query.toLowerCase();
    
    // Helper helper for random selection
    const choose = (arr) => arr[Math.floor(Math.random() * arr.length)];

    // 1. DETEKSI PENYAKIT DETAIL (Kecuali Sehat)
    for (const d of DISEASES_DB) {
        if (d.nama !== "Sehat" && q_lower.includes(d.nama.toLowerCase())) {
            let obat_info = "";
            if (d.obat_list && d.obat_list.length > 0) {
                obat_info = "\n\n**Rekomendasi Obat:**\n" + d.obat_list.map(o => `💊 **${o.nama_obat}** (Dosis: ${o.dosis} | Cara: ${o.cara_penggunaan})`).join("\n");
            }
            
            return (
                `Oh ya Kak, terkait penyakit **${d.nama}** (${d.nama_ilmiah}), berikut Leli jelaskan detailnya:\n\n` +
                `⚠️ **Gejala yang Terlihat:**\n${d.gejala}\n\n` +
                `🔍 **Penyebab Utama:**\n${d.penyebab}\n\n` +
                `🛠️ **Langkah Penanganan:**\n${d.penanganan}\n\n` +
                `🛡️ **Cara Pencegahan:**\n${d.pencegahan}${obat_info}\n\n` +
                `Saran Leli, segera pisahkan (isolasi) lele yang sakit ke wadah karantina ya Kak agar tidak menular ke lele sehat lainnya!`
            );
        }
    }
    
    // 2. KATEGORI BUDIDAYA UMUM
    if (CHATBOT_KEYWORDS.pakan.some(kw => q_lower.includes(kw))) {
        const pakan_variations = [
            "Wah, ngomongin soal pakan lele memang sangat penting Kak! Biar FCR-nya bagus dan cepat panen, ini tips dari Leli:\n\n" +
            "• **Frekuensi**: Berikan 2–3 kali sehari (pagi, sore, malam). Malam hari porsinya bisa agak banyak karena lele aktif di malam hari!\n" +
            "• **Takaran**: Sekitar 3–5% dari total berat lele di kolam Kakak.\n" +
            "• **Protein**: Pilih pelet dengan protein minimal 30% biar dagingnya padat.\n" +
            "• **Bahaya Overfeeding**: Jangan sampai berlebihan ya Kak, karena sisa pakan yang mengendap di dasar kolam bisa jadi racun amonia dan bikin lele kembung/terapung.\n\n" +
            "Mau tanya resep pakan alternatif atau cara ngitung kebutuhan pakan hariannya, Kak?",
            
            "Nutrisi pakan menentukan kecepatan lele tumbuh besar Kak! Ini aturan main pakan dari Leli:\n\n" +
            "• **Bibit (di bawah 5cm)**: Beri pakan tipe tepung/fine-grain berulang 4-5 kali sehari dalam porsi kecil.\n" +
            "• **Lele Dewasa**: Beri pelet apung diameter sesuai bukaan mulut lele. Cukup 2-3 kali sehari.\n" +
            "• **Waktu Terbaik**: Pagi jam 7 dan sore jam 5. Hindari memberi makan saat matahari terik di jam 12-1 siang karena suhu panas menurunkan nafsu makan lele.\n\n" +
            "Mau konsultasi cara fermentasi pelet agar lele lebih mudah mencerna pakan, Kak?"
        ];
        return choose(pakan_variations);
    }
    
    if (CHATBOT_KEYWORDS.air.some(kw => q_lower.includes(kw))) {
        const air_variations = [
            "Air kolam itu rumah bagi lele Kak, jadi kalau airnya bersih, lele pasti nyaman dan nafsu makan tinggi! Ini panduannya:\n\n" +
            "• **Kadar pH**: Jaga di kisaran 6.5 sampai 8.0. Kalau terlalu asam, lele gampang sakit.\n" +
            "• **Suhu**: Idealnya 25–30°C. Cuaca pancaroba biasanya bikin suhu tidak stabil.\n" +
            "• **Oksigen (DO)**: Minimal 3-5 mg/L. Kalau lele banyak megap-megap di permukaan pagi hari, itu tandanya kekurangan oksigen.\n" +
            "• **Solusi**: Lakukan penggantian air kolam sebanyak 20-30% secara berkala dan berikan probiotik EM4 untuk mengurai sisa kotoran.\n\n" +
            "Warna air kolam Kakak sekarang hijau, cokelat, atau hitam pekat?",
            
            "Kunci sukses budidaya lele itu sebenarnya di 'Manajemen Air' Kak. Lele yang sakit biasanya karena air kolamnya bermasalah. Leli sarankan:\n\n" +
            "1. **Buang Lumpur Dasar**: Endapan sisa pakan di dasar kolam menghasilkan gas amonia beracun. Buang secara rutin (sifon).\n" +
            "2. **Aplikasi Probiotik**: Masukkan probiotik 1-2 minggu sekali untuk mengurai sisa bahan organik.\n" +
            "3. **Ganti Air**: Jangan ganti seluruh air sekaligus! Cukup buang 20% air dasar kolam lalu isi air baru agar ikan tidak stres akibat perubahan suhu mendadak."
        ];
        return choose(air_variations);
    }
    
    if (CHATBOT_KEYWORDS.kolam.some(kw => q_lower.includes(kw))) {
        return (
            "Persiapan kolam yang matang itu kunci kesuksesan budidaya Kak! Ini tips mempersiapkannya:\n\n" +
            "1. **Jemur Kolam**: Keringkan kolam selama 3-5 hari biar bakteri jahat mati.\n" +
            "2. **Kapur Dolomit**: Taburkan 100-200 gram/m² untuk menetralkan pH tanah/dinding.\n" +
            "3. **Fermentasi Air**: Isi air setinggi 30-40 cm dulu, campurkan probiotik, lalu diamkan 5-7 hari sampai air berwarna kehijauan (tumbuh plankton alami).\n" +
            "4. **Ketinggian**: Setelah plankton tumbuh, tambahkan air sampai 80-100 cm baru tebar bibit.\n\n" +
            "Kolam Kakak tipe apa nih? Kolam terpal, semen, atau tanah?"
        );
    }
    
    if (CHATBOT_KEYWORDS.bibit.some(kw => q_lower.includes(kw))) {
        return (
            "Memilih bibit lele yang unggul bakal meminimalkan kematian dini Kak! Ini ciri-ciri bibit berkualitas:\n\n" +
            "• **Aktif**: Berenang lincah menantang arus air.\n" +
            "• **Seragam**: Ukuran tubuhnya mirip (misal 5-7 cm) biar tidak saling serang.\n" +
            "• **Fisik Sempurna**: Kulit mulus, kumis utuh, dan tidak ada luka.\n" +
            "• **Tips Tebar**: Jangan langsung dituang ya Kak! Apungkan wadah bibit di kolam selama 15 menit agar lele menyesuaikan diri dengan suhu air baru (aklimatisasi).\n\n" +
            "Ada rencana mau tebar berapa ribu ekor bibit, Kak?"
        );
    }
    
    if (CHATBOT_KEYWORDS.panen.some(kw => q_lower.includes(kw))) {
        return (
            "Momen panen pasti yang paling ditunggu-tunggu! Biar hasil panen Kakak melimpah dan untung maksimal, ini rahasianya:\n\n" +
            "• **Ukuran Pasar**: Biasanya isi 8-10 ekor per kilogram (panjang ±20 cm).\n" +
            "• **Waktu Budidaya**: Cukup 60-90 hari saja jika pakannya rajin dan berkualitas.\n" +
            "• **Tips Penting**: Puasakan lele selama 24 jam sebelum dipanen. Ini berguna biar lambung lele kosong, lele tidak gampang muntah, dan dagingnya segar/tidak amis saat dikirim!\n\n" +
            "Pemasarannya sudah aman kan Kak? Biasanya dijual ke tengkulak atau langsung ke warung pecel lele?"
        );
    }

    if (CHATBOT_KEYWORDS.probiotik.some(kw => q_lower.includes(kw))) {
        return (
            "Probiotik (seperti EM4 Perikanan atau Bacillus) sangat berguna untuk kesehatan pencernaan lele dan penguraian amonia di kolam Kak. Ini panduan menggunakannya:\n\n" +
            "• **Campur Pakan**: Larutkan 1 tutup botol EM4 + 1 sendok makan molase/gula dalam secangkir air. Bibiskan (semprotkan) secara merata ke 1 kg pelet, diamkan 15 menit agar meresap baru berikan ke lele.\n" +
            "• **Kualitas Air**: Tuangkan probiotik yang telah diaktifkan ke air kolam setiap 1-2 minggu sekali untuk menjaga kestabilan plankton baik.\n\n" +
            "Apakah Kakak sudah mulai memakai probiotik di kolam saat ini?"
        );
    }

    if (CHATBOT_KEYWORDS.garam.some(kw => q_lower.includes(kw))) {
        return (
            "Garam krosok (garam ikan non-yodium) adalah 'obat dewa' yang murah meriah untuk lele Kak! Kegunaannya meliputi:\n\n" +
            "1. **Pencegahan Stres**: Menjaga keseimbangan osmoregulasi lele saat ganti air kolam atau cuaca ekstrem.\n" +
            "2. **Desinfektan Alami**: Membunuh parasit kulit dan mencegah spora jamur tumbuh.\n" +
            "3. **Dosis Aman**: \n" +
            "   • Pencegahan: 500 gram sampai 1 kg garam per 1.000 liter air kolam.\n" +
            "   • Pengobatan Jamur: Rendam lele yang sakit dalam wadah khusus dengan dosis 10-20 gram garam per liter air selama 5-10 menit.\n\n" +
            "Pastikan menggunakan garam krosok kasar kasar ya Kak, jangan garam dapur beryodium!"
        );
    }

    if (CHATBOT_KEYWORDS.kanibal.some(kw => q_lower.includes(kw))) {
        return (
            "Masalah lele saling memakan (kanibalisme) biasanya dipicu oleh perbedaan ukuran yang mencolok atau pakan yang telat Kak. Solusi terbaik dari Leli:\n\n" +
            "1. **Grading / Sortasi**: Lakukan penyortiran ukuran lele secara rutin setiap 2 minggu sekali. Pisahkan lele yang berukuran bongsor, sedang, dan kerdil ke kolam berbeda.\n" +
            "2. **Pemberian Pakan Tepat Waktu**: Lele yang kelaparan akan langsung berburu kawannya yang lebih kecil. Jaga konsistensi jadwal makan lele.\n" +
            "3. **Padat Tebar yang Sesuai**: Jangan terlalu padat tebar (ideal bibit 100-150 ekor per m² pada air setinggi 80 cm) agar tingkat kompetisi ruang tidak terlalu tinggi.\n\n" +
            "Apakah lele Kakak saat ini ukurannya sudah mulai terlihat tidak seragam?"
        );
    }

    if (CHATBOT_KEYWORDS.biaya.some(kw => q_lower.includes(kw))) {
        return (
            "Mengelola pengeluaran modal budidaya lele itu penting agar Kakak bisa untung maksimal! Ini tips dari Leli:\n\n" +
            "• **Feed Conversion Ratio (FCR)**: Targetkan FCR di bawah 1.1. Artinya, untuk menghasilkan 1 kg daging lele, Kakak hanya butuh menghabiskan pelet maksimal 1.1 kg.\n" +
            "• **Pakan Alternatif**: Untuk menghemat biaya pakan komersial (pelet pabrik), Kakak bisa selingi dengan pakan alternatif berprotein tinggi seperti maggot BSF, ampas tahu fermentasi, atau ikan rucah rebus.\n" +
            "• **Biaya Bibit & Listrik**: Catat semua pengeluaran dari awal pembelian bibit, biaya listrik aerator/pompa air, hingga vitamin agar pembukuan panen Kakak rapi.\n\n" +
            "Berapa ukuran kolam Kakak dan berapa banyak bibit yang sedang dipelihara? Mari kita bantu hitung estimasi biayanya!"
        );
    }

    // 3. KONDISI SEHAT (Sehat / Normal / Baik / Segar)
    if (CHATBOT_KEYWORDS.sehat.some(kw => q_lower.includes(kw))) {
        return (
            "Alhamdulillah! Senang sekali mendengarnya. Kondisi lele Kakak terpantau **Sehat** walafiat. 🐟💚\n\n" +
            "Tetap pertahaman ya Kak! Jangan lupa rutin ganti air kolam sekitar 20-30% setiap minggu, berikan pakan berkualitas secara konsisten, dan selalu jaga kebersihan kolam."
        );
    }
    
    // 4. PERKENALAN DIRI (Self-Introduction)
    if (CHATBOT_KEYWORDS.intro.some(kw => q_lower.includes(kw))) {
        const intro_variations = [
            "Halo Kak! Kenalin, aku **Leli** (asisten AI ahli budidaya ikan lele) 🐟✨\n\n" +
            "Aku diciptakan khusus untuk menemani Kakak dalam merawat kolam lele kesayangan. Kakak bisa tanya-tanya aku tentang:\n" +
            "• **Diagnosis penyakit lele** (seperti Aeromonas, Jamur, Malnutrisi, atau Overfeeding)\n" +
            "• **Tips pakan** yang hemat dan bergizi\n" +
            "• **Menjaga kualitas air** biar lele nggak stres\n" +
            "• **Persiapan kolam** dari awal tebar sampai panen raya!\n\n" +
            "Ada yang bisa Leli bantu hari ini biar lele kita sehat dan cepat besar? 😊",
            
            "Hai Kak! Aku **Leli**, asisten budidaya lele pintar kamu di sini. 🐟👋\n\n" +
            "Leli siap bantu Kakak memecahkan masalah kolam, mengoptimalkan pakan, mengenali gejala penyakit lele secara dini, hingga tips sortasi lele agar tidak saling kanibal.\n\n" +
            "Apa yang ingin Kakak tanyakan hari ini?"
        ];
        return choose(intro_variations);
    }
    
    // 5. SAPAAN UMUM (Common Greetings)
    if (CHATBOT_KEYWORDS.greeting.some(kw => q_lower.trim() === kw || q_lower.startsWith(kw + " "))) {
        const greeting_variations = [
            "Halo Kak! Senang banget bisa ketemu. 😊\n\n" +
            "Semoga hari ini kolam lele Kakak dalam kondisi prima ya! Leli siap bantu jawab pertanyaan seputar budidaya, penyakit lele, pakan, atau kualitas air kolam. Kakak mau diskusi tentang apa hari ini?",
            
            "Hai Kak! Senang sekali menyapa Kakak hari ini. Bagaimana kondisi kolam lele Anda? 🐟✨\n\n" +
            "Ada yang bisa Leli bantu? Tanyakan saja seputar pakan, persiapan kolam, air, atau penyakit lele ya!",
            
            "Halo Kak! Leli di sini siap menemani diskusi budidaya lele Anda. Semoga lele Anda tumbuh sehat dan nafsu makan kuat! Ada kendala apa di kolam hari ini? 😊"
        ];
        return choose(greeting_variations);
    }
    
    // 6. JAWABAN LUAR KONTEKS (Out of Context Router)
    if (CHATBOT_KEYWORDS.outOfContext.some(kw => q_lower.includes(kw)) || q_lower.split(" ").length > 5) {
        const out_of_context_variations = [
            "Wah, pertanyaan menarik Kak! 😄\n\n" +
            "Sebenarnya, Leli adalah asisten khusus budidaya lele. Tapi kalau Kakak penasaran tentang itu, sepemahaman Leli, hal tersebut cukup ramai dibahas banyak orang akhir-akhir ini!\n\n" +
            "Meskipun Leli ahli di dunia air dan kolam lele, kalau Kakak mau ngobrol santai Leli senang-senang saja. Tapi jangan lupa pantau kolam lelenya juga ya Kak! Ada kendala apa di kolam lele Kakak hari ini?",
            
            "Hehe, seru juga nih pertanyaannya Kak! 😆 Tapi sebagai asisten budidaya lele, Leli lebih mengerti tentang air kolam, bibit unggul, dan penyakit lele.\n\n" +
            "Bagaimana kalau kita kembali membahas cara merawat lele agar cepat panen dan sehat walafiat? Kolam lele Kakak saat ini aman-aman saja kan?"
        ];
        return choose(out_of_context_variations);
    }
    
    // 7. DEFAULT RESPOND
    const default_variations = [
        "Halo Kak! Aku Leli, asisten AI budidaya ikan lele. 😊\n\n" +
        "Ada yang bisa Leli bantu untuk kolam lele Kakak hari ini? Kakak bisa tanya soal:\n" +
        "• **Penyakit lele** (seperti Malnutrisi, Jamur, Overfeeding, atau Aeromonas)\n" +
        "• **Manajemen Air & Pakan**\n" +
        "• **Cara Tebar Bibit & Panen**",
        
        "Hai Kak! Leli di sini untuk membantu Anda mengelola peternakan lele. 🐟✨\n\n" +
        "Silakan ajukan pertanyaan seputar:\n" +
        "• Berapa porsi pakan yang tepat?\n" +
        "• Cara mengobati jamur air?\n" +
        "• Prosedur fermentasi EM4?\n" +
        "Tuliskan pertanyaan Kakak di bawah ya!"
    ];
    return choose(default_variations);
}g estimasi biayanya!"
        );
    }
    
    // 5. JAWABAN LUAR KONTEKS (Out of Context Router)
    if (CHATBOT_KEYWORDS.outOfContext.some(kw => q_lower.includes(kw)) || q_lower.split(" ").length > 5) {
        const out_of_context_variations = [
            "Wah, pertanyaan menarik Kak! 😄\n\n" +
            "Sebenarnya, Leli adalah asisten khusus budidaya lele. Tapi kalau Kakak penasaran tentang itu, sepemahaman Leli, hal tersebut cukup ramai dibahas banyak orang akhir-akhir ini!\n\n" +
            "Meskipun Leli ahli di dunia air dan kolam lele, kalau Kakak mau ngobrol santai Leli senang-senang saja. Tapi jangan lupa pantau kolam lelenya juga ya Kak! Ada kendala apa di kolam lele Kakak hari ini?",
            
            "Hehe, seru juga nih pertanyaannya Kak! 😆 Tapi sebagai asisten budidaya lele, Leli lebih mengerti tentang air kolam, bibit unggul, dan penyakit lele.\n\n" +
            "Bagaimana kalau kita kembali membahas cara merawat lele agar cepat panen dan sehat walafiat? Kolam lele Kakak saat ini aman-aman saja kan?"
        ];
        return choose(out_of_context_variations);
    }
    
    // 6. DEFAULT RESPOND
    const default_variations = [
        "Halo Kak! Aku Leli, asisten AI budidaya ikan lele. 😊\n\n" +
        "Ada yang bisa Leli bantu untuk kolam lele Kakak hari ini? Kakak bisa tanya soal:\n" +
        "• **Penyakit lele** (seperti Malnutrisi, Jamur, Overfeeding, atau Aeromonas)\n" +
        "• **Manajemen Air & Pakan**\n" +
        "• **Cara Tebar Bibit & Panen**",
        
        "Hai Kak! Leli di sini untuk membantu Anda mengelola peternakan lele. 🐟✨\n\n" +
        "Silakan ajukan pertanyaan seputar:\n" +
        "• Berapa porsi pakan yang tepat?\n" +
        "• Cara mengobati jamur air?\n" +
        "• Prosedur fermentasi EM4?\n" +
        "Tuliskan pertanyaan Kakak di bawah ya!"
    ];
    return choose(default_variations);
}

function scrollChatToBottom() {
    const messagesEl = document.getElementById("chat-messages-container");
    requestAnimationFrame(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    });
}

/* ─────────────────────────────────────────────────────────────────────────
   KNOWLEDGE BASE & ARTICLES
   ───────────────────────────────────────────────────────────────────────── */
function displayDiseases(diseases) {
    const grid = document.getElementById("disease-directory-grid");
    if (!grid) return;
    
    grid.innerHTML = "";
    const actualDiseases = diseases.filter(d => d.nama !== "Sehat");
    
    actualDiseases.forEach(d => {
        const card = document.createElement("div");
        card.className = "glass-card disease-card";
        
        let icon = "🐟";
        const nameLower = d.nama.toLowerCase();
        if (nameLower.includes("aeromonas")) icon = "🦠";
        else if (nameLower.includes("jamur")) icon = "🍄";
        else if (nameLower.includes("malnutrisi")) icon = "🦴";
        else if (nameLower.includes("overfeeding")) icon = "🎈";
        
        card.innerHTML = `
            <div class="disease-header">
                <h3>${d.nama.replace("_", " ")}</h3>
                <span class="feature-icon" style="margin-bottom:0;width:35px;height:35px;font-size:16px;">${icon}</span>
            </div>
            <div class="disease-sci">${d.nama_ilmiah || "Bacterial Infection"}</div>
            <p style="font-size: 13px; color: var(--text-muted); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                ${d.deskripsi}
            </p>
        `;
        card.addEventListener("click", () => {
            showDiseaseDetailModal(d);
        });
        grid.appendChild(card);
    });
}

function displayArticles(articles) {
    const grid = document.getElementById("articles-directory-grid");
    if (!grid) return;
    
    grid.innerHTML = "";
    articles.forEach(a => {
        const card = document.createElement("div");
        card.className = "glass-card";
        card.style.display = "flex";
        card.style.flexDirection = "column";
        card.innerHTML = `
            <span class="hero-tagline" style="align-self:flex-start; margin-bottom:12px; font-size:11px;">${a.kategori}</span>
            <h3 style="margin-bottom:10px; font-size:18px;">${a.judul}</h3>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom:20px; flex:1; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;">
                ${a.konten}
            </p>
            <button class="btn btn-secondary" style="padding:8px 16px; font-size:12px; align-self:flex-start;">Baca Selengkapnya</button>
        `;
        
        card.querySelector("button").addEventListener("click", () => {
            showArticleModal(a);
        });
        grid.appendChild(card);
    });
}

function showDiseaseDetailModal(d) {
    const modal = document.getElementById("disease-detail-modal");
    
    document.getElementById("modal-disease-name").innerText = d.nama.replace("_", " ");
    document.getElementById("modal-disease-sci").innerText = d.nama_ilmiah || "";
    document.getElementById("modal-disease-desc").innerText = d.deskripsi;
    document.getElementById("modal-disease-symptoms").innerText = d.gejala;
    document.getElementById("modal-disease-cause").innerText = d.penyebab;
    document.getElementById("modal-disease-prevention").innerText = d.pencegahan;
    document.getElementById("modal-disease-treatment").innerText = d.penanganan;
    
    // Explicitly restore display values for all sections
    document.getElementById("modal-disease-symptoms").parentNode.style.display = "block";
    document.getElementById("modal-disease-cause").parentNode.style.display = "block";
    document.getElementById("modal-disease-prevention").parentNode.style.display = "block";
    document.getElementById("modal-disease-treatment").parentNode.style.display = "block";
    document.getElementById("modal-disease-medicines").parentNode.style.display = "block";
    
    const medContainer = document.getElementById("modal-disease-medicines");
    medContainer.innerHTML = "";
    
    if (d.obat_list && d.obat_list.length > 0) {
        d.obat_list.forEach(m => {
            const mEl = document.createElement("div");
            mEl.className = "glass-card";
            mEl.style.padding = "16px";
            mEl.style.borderStyle = "dashed";
            mEl.innerHTML = `
                <h4 style="color:var(--primary); margin-bottom:6px;">💊 ${m.nama_obat}</h4>
                <p style="font-size:13px; margin-bottom:4px;"><strong>Dosis:</strong> ${m.dosis}</p>
                <p style="font-size:13px; margin-bottom:4px;"><strong>Cara Penggunaan:</strong> ${m.cara_penggunaan}</p>
                ${m.catatan ? `<p style="font-size:12px; color:var(--accent);">* ${m.catatan}</p>` : ""}
            `;
            medContainer.appendChild(mEl);
        });
    } else {
        medContainer.innerHTML = `<p style="font-size:13px; color:var(--text-muted);">Tidak ada obat kimia khusus. Gunakan penanganan alami dan perbaiki air.</p>`;
    }
    
    modal.classList.add("active");
    
    modal.querySelector(".modal-close").onclick = () => {
        modal.classList.remove("active");
    };
    
    modal.onclick = (e) => {
        if (e.target === modal) {
            modal.classList.remove("active");
        }
    };
}

function showArticleModal(a) {
    const modal = document.getElementById("disease-detail-modal");
    
    document.getElementById("modal-disease-name").innerText = a.judul;
    document.getElementById("modal-disease-sci").innerText = a.kategori;
    document.getElementById("modal-disease-desc").innerText = "";
    
    document.getElementById("modal-disease-symptoms").parentNode.style.display = "none";
    document.getElementById("modal-disease-cause").parentNode.style.display = "none";
    document.getElementById("modal-disease-prevention").parentNode.style.display = "none";
    document.getElementById("modal-disease-treatment").parentNode.style.display = "none";
    document.getElementById("modal-disease-medicines").parentNode.style.display = "none";
    
    const formattedContent = a.konten.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    document.getElementById("modal-disease-desc").innerHTML = formattedContent;
    
    modal.classList.add("active");
    
    const cleanClose = () => {
        modal.classList.remove("active");
        document.getElementById("modal-disease-symptoms").parentNode.style.display = "block";
        document.getElementById("modal-disease-cause").parentNode.style.display = "block";
        document.getElementById("modal-disease-prevention").parentNode.style.display = "block";
        document.getElementById("modal-disease-treatment").parentNode.style.display = "block";
        document.getElementById("modal-disease-medicines").parentNode.style.display = "block";
    };
    
    modal.querySelector(".modal-close").onclick = cleanClose;
    modal.onclick = (e) => {
        if (e.target === modal) cleanClose();
    };
}

/* ─────────────────────────────────────────────────────────────────────────
   HISTORY LOGS
   ───────────────────────────────────────────────────────────────────────── */
function loadDetectionHistory() {
    const tableBody = document.getElementById("history-table-body");
    tableBody.innerHTML = "";
    
    if (state.history.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:24px;">Belum ada riwayat deteksi.</td></tr>`;
        return;
    }
    
    const sortedHistory = [...state.history].reverse();
    sortedHistory.forEach(log => {
        const tr = document.createElement("tr");
        const date = new Date(log.created_at).toLocaleDateString("id-ID", { dateStyle: "medium" });
        
        let statusBadge = `<span class="result-badge badge-sehat" style="padding:2px 8px;font-size:10px;">Selesai</span>`;
        
        tr.innerHTML = `
            <td style="font-weight:600;">#${log.id}</td>
            <td>${date}</td>
            <td style="text-transform: capitalize;">${log.penyakit_terdeteksi.replace("_", " ")}</td>
            <td>${log.confidence_persen}</td>
            <td>${statusBadge}</td>
            <td>
                <button class="btn btn-secondary btn-view-log" style="padding:6px 12px; font-size:11px; margin:0;">Detail</button>
            </td>
        `;
        
        tr.querySelector(".btn-view-log").addEventListener("click", () => {
            showSection("detection");
            displayDetectionResult(log);
            const previewContainer = document.querySelector(".preview-container");
            const previewImg = document.querySelector(".preview-img");
            previewImg.src = log.image;
            previewContainer.style.display = "block";
            document.getElementById("btn-analyze-ai").style.display = "none";
        });
        
        tableBody.appendChild(tr);
    });
}
