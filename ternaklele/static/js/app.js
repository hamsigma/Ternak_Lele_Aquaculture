/**
 * Core Application Logic untuk Ternak Lele Web SPA
 * Mengintegrasikan Django REST Framework API dengan UI Glassmorphic
 */

const API_URLS = {
    register: "/api/auth/register/",
    login: "/api/auth/login/",
    profile: "/api/auth/profile/",
    upload: "/api/detection/upload/",
    result: (id) => `/api/detection/result/${id}/`,
    history: "/api/detection/history/",
    chat: "/api/chatbot/",
    chatSessions: "/api/chatbot/sessions/",
    chatSessionDetail: (id) => `/api/chatbot/sessions/${id}/`,
    penyakit: "/api/knowledge/penyakit/",
    artikel: "/api/knowledge/artikel/",
};

// Application State
const state = {
    token: localStorage.getItem("lele_token") || null,
    user: null,
    diseases: [],
    articles: [],
    activeSessionId: null,
    selectedFile: null,
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
    if (state.token) {
        fetchProfile();
    } else {
        showSection("landing");
        updateSidebarUI(false);
    }
    
    // Load public data
    loadKnowledgeBase();
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
    }
    
    // Update sidebar active class
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        const link = item.querySelector("a");
        if (link && link.getAttribute("data-section") === sectionId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });
    
    // Toggle chatbot body lock — prevents page scroll that hides chat input
    if (sectionId === "chatbot") {
        document.body.classList.add("chatbot-active");
    } else {
        document.body.classList.remove("chatbot-active");
    }
    
    // Section-specific loads
    if (sectionId === "dashboard" && state.token) {
        loadDashboardStats();
    } else if (sectionId === "history" && state.token) {
        loadDetectionHistory();
    } else if (sectionId === "chatbot" && state.token) {
        loadChatSessions();
    }
    
    // Scroll to top (skip for chatbot — it manages its own scroll)
    if (sectionId !== "chatbot") {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}

/* ─────────────────────────────────────────────────────────────────────────
   AUTHENTICATION LOGIC
   ───────────────────────────────────────────────────────────────────────── */
function setupAuthForms() {
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const formLogin = document.getElementById("form-login");
    const formRegister = document.getElementById("form-register");
    
    tabLogin.addEventListener("click", () => {
        tabLogin.classList.add("active");
        tabRegister.classList.remove("active");
        formLogin.style.display = "block";
        formRegister.style.display = "none";
    });
    
    tabRegister.addEventListener("click", () => {
        tabRegister.classList.add("active");
        tabLogin.classList.remove("active");
        formRegister.style.display = "block";
        formLogin.style.display = "none";
    });
    
    // Login Submit
    formLogin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = formLogin.querySelector("[name='username']").value;
        const password = formLogin.querySelector("[name='password']").value;
        
        try {
            const response = await fetch(API_URLS.login, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            if (response.ok) {
                state.token = data.access;
                localStorage.setItem("lele_token", data.access);
                showToast("Selamat datang kembali!", "success");
                await fetchProfile();
                showSection("dashboard");
            } else {
                showToast(data.detail || "Nama pengguna atau kata sandi salah.", "error");
            }
        } catch (err) {
            showToast("Gagal terhubung ke server backend.", "error");
        }
    });
    
    // Register Submit
    formRegister.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = formRegister.querySelector("[name='username']").value;
        const email = formRegister.querySelector("[name='email']").value;
        const no_telepon = formRegister.querySelector("[name='no_telepon']").value;
        const lokasi_kolam = formRegister.querySelector("[name='lokasi_kolam']").value;
        const password = formRegister.querySelector("[name='password']").value;
        
        try {
            const response = await fetch(API_URLS.register, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, no_telepon, lokasi_kolam, password, role: "pembudidaya" })
            });
            
            const data = await response.json();
            if (response.ok) {
                showToast("Registrasi berhasil! Silakan masuk.", "success");
                // Switch to login tab
                tabLogin.click();
                formLogin.querySelector("[name='username']").value = username;
            } else {
                const keys = Object.keys(data);
                showToast(data[keys[0]][0] || "Gagal melakukan registrasi.", "error");
            }
        } catch (err) {
            showToast("Gagal terhubung ke server backend.", "error");
        }
    });
}

async function fetchProfile() {
    try {
        const response = await fetch(API_URLS.profile, {
            headers: { "Authorization": `Bearer ${state.token}` }
        });
        
        if (response.status === 401) {
            logout();
            return;
        }
        
        const data = await response.json();
        if (response.ok) {
            state.user = data;
            updateSidebarUI(true);
            updateDashboardWelcome();
        }
    } catch (err) {
        console.error("Gagal memuat profil:", err);
    }
}

function updateSidebarUI(isAuthenticated) {
    const sidebar = document.querySelector(".sidebar");
    const widget = document.querySelector(".user-profile-widget");
    const loginNavItem = document.getElementById("nav-login-item");
    const dashboardNavItem = document.getElementById("nav-dashboard-item");
    const historyNavItem = document.getElementById("nav-history-item");
    
    if (isAuthenticated && state.user) {
        widget.style.display = "flex";
        widget.querySelector(".user-avatar").innerText = state.user.username.substring(0, 2).toUpperCase();
        widget.querySelector(".user-name").innerText = state.user.username;
        widget.querySelector(".user-role").innerText = state.user.role === "pakar" ? "Pakar Perikanan" : "Pembudidaya";
        
        if (loginNavItem) loginNavItem.style.display = "none";
        if (dashboardNavItem) dashboardNavItem.style.display = "block";
        if (historyNavItem) historyNavItem.style.display = "block";
    } else {
        widget.style.display = "none";
        if (loginNavItem) loginNavItem.style.display = "block";
        if (dashboardNavItem) dashboardNavItem.style.display = "none";
        if (historyNavItem) historyNavItem.style.display = "none";
    }
}

function updateDashboardWelcome() {
    const welcomeName = document.getElementById("welcome-name");
    const profileLoc = document.getElementById("profile-location");
    if (welcomeName && state.user) {
        welcomeName.innerText = state.user.username;
    }
    if (profileLoc && state.user) {
        profileLoc.innerText = state.user.lokasi_kolam || "Lokasi kolam belum diisi";
    }
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem("lele_token");
    updateSidebarUI(false);
    showToast("Anda telah keluar.", "info");
    showSection("landing");
}

/* ─────────────────────────────────────────────────────────────────────────
   DASHBOARD STATS
   ───────────────────────────────────────────────────────────────────────── */
async function loadDashboardStats() {
    try {
        const response = await fetch(API_URLS.history, {
            headers: { "Authorization": `Bearer ${state.token}` }
        });
        if (response.ok) {
            const data = await response.json();
            const logs = data.results || data;
            const totalDetections = logs.length || 0;
            const healthyCount = logs.filter(l => l.penyakit_terdeteksi === "Sehat").length || 0;
            const diseaseCount = totalDetections - healthyCount;
            
            document.getElementById("stat-total").innerText = totalDetections;
            document.getElementById("stat-sehat").innerText = healthyCount;
            document.getElementById("stat-sakit").innerText = diseaseCount;
        }
    } catch (e) {
        console.error("Gagal mengambil statistik dashboard:", e);
    }
}

/* ─────────────────────────────────────────────────────────────────────────
   DETEKSI PENYAKIT AI LOGIC
   ───────────────────────────────────────────────────────────────────────── */
function setupUpload() {
    const uploadArea = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("file-input");
    const previewContainer = document.querySelector(".preview-container");
    const previewImg = document.querySelector(".preview-img");
    const btnSubmit = document.getElementById("btn-analyze-ai");
    const resultContainer = document.querySelector(".result-container");
    
    uploadArea.addEventListener("click", () => {
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("drag-over");
    });
    
    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("drag-over");
    });
    
    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("drag-over");
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
        // Validation size
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
    
    btnSubmit.addEventListener("click", async () => {
        if (!state.selectedFile) return;
        
        // Loader
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = `<div class="loader-spinner" style="width:20px;height:20px;margin:0;"></div> Memproses...`;
        
        const formData = new FormData();
        formData.append("image", state.selectedFile);
        
        try {
            const response = await fetch(API_URLS.upload, {
                method: "POST",
                headers: { "Authorization": `Bearer ${state.token}` },
                body: formData
            });
            
            const data = await response.json();
            if (response.ok) {
                showToast("Gambar terunggah, menganalisis...", "info");
                pollDetectionResult(data.id);
            } else {
                showToast(data.image ? data.image[0] : "Gagal mengunggah gambar.", "error");
                resetAnalyzeButton();
            }
        } catch (err) {
            showToast("Koneksi gagal saat mengunggah.", "error");
            resetAnalyzeButton();
        }
    });
}

function resetAnalyzeButton() {
    const btnSubmit = document.getElementById("btn-analyze-ai");
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = `🐟 Mulai Analisis AI`;
}

async function pollDetectionResult(logId) {
    let attempts = 0;
    const interval = setInterval(async () => {
        attempts++;
        if (attempts > 30) {
            clearInterval(interval);
            showToast("Waktu analisis habis. Cek riwayat beberapa saat lagi.", "error");
            resetAnalyzeButton();
            return;
        }
        
        try {
            const response = await fetch(API_URLS.result(logId), {
                headers: { "Authorization": `Bearer ${state.token}` }
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.status_proses === "done") {
                    clearInterval(interval);
                    showToast("Analisis AI selesai!", "success");
                    displayDetectionResult(result);
                    resetAnalyzeButton();
                } else if (result.status_proses === "failed") {
                    clearInterval(interval);
                    showToast("Analisis AI gagal diproses.", "error");
                    resetAnalyzeButton();
                }
            }
        } catch (e) {
            console.error("Polling error:", e);
        }
    }, 1000);
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
    // stroke-dasharray is 345.5.
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
            item.querySelector(".prob-bar").style.width = `${pct}%`;
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
    showSection("chatbot");
    const messageInput = document.getElementById("chat-message-input");
    if (diseaseName === "Sehat") {
        messageInput.value = "Halo Leli, bagaimanakah cara menjaga kualitas air kolam lele agar ikan tetap sehat?";
    } else {
        messageInput.value = `Halo Leli, ikan lele saya baru saja didiagnosis terkena penyakit ${diseaseName.replace("_", " ")}. Bagaimana penanganan darurat yang bisa saya lakukan?`;
    }
    messageInput.focus();
}

/* ─────────────────────────────────────────────────────────────────────────
   CHATBOT RAG LOGIC (LELI ASISTEN)
   ───────────────────────────────────────────────────────────────────────── */
function setupChat() {
    const listContainer = document.getElementById("chat-sessions-list");
    const btnNewSession = document.getElementById("btn-new-session");
    const messagesEl = document.getElementById("chat-messages-container");
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

async function loadChatSessions() {
    const listContainer = document.getElementById("chat-sessions-list");
    listContainer.innerHTML = `<div class="loader-spinner" style="width:30px;height:30px;"></div>`;
    
    try {
        const response = await fetch(API_URLS.chatSessions, {
            headers: { "Authorization": `Bearer ${state.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const sessions = data.results || data;
            listContainer.innerHTML = "";
            
            if (sessions.length === 0) {
                listContainer.innerHTML = `<p style="font-size: 13px; color: var(--text-muted); text-align: center; margin-top:20px;">Belum ada sesi percakapan.</p>`;
                startNewChatSession(); // Auto-create first session
                return;
            }
            
            sessions.forEach(session => {
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
            if (!state.activeSessionId && sessions.length > 0) {
                openChatSession(sessions[0].id);
            }
        }
    } catch (e) {
        listContainer.innerHTML = `<p style="color:var(--danger); font-size:12px;">Gagal memuat sesi chat.</p>`;
    }
}

function startNewChatSession() {
    state.activeSessionId = null;
    
    // Clear chat bubbles
    const messagesEl = document.getElementById("chat-messages-container");
    messagesEl.innerHTML = `
        <div class="chat-bubble chat-bubble-ai">
            Halo! Saya Leli, asisten virtual budidaya ikan lele Anda. Ada yang bisa saya bantu hari ini seputar kesehatan kolam, nutrisi pakan, atau penyakit lele Anda?
            <div class="chat-bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
    
    // Highlight items
    document.querySelectorAll(".session-item").forEach(item => item.classList.remove("active"));
}

async function openChatSession(sessionId) {
    state.activeSessionId = sessionId;
    
    // Highlight item
    document.querySelectorAll(".session-item").forEach(item => {
        item.classList.remove("active");
    });
    
    // Load messages
    const messagesEl = document.getElementById("chat-messages-container");
    messagesEl.innerHTML = `<div class="loader-spinner" style="width:40px;height:40px;"></div>`;
    
    try {
        const response = await fetch(API_URLS.chatSessionDetail(sessionId), {
            headers: { "Authorization": `Bearer ${state.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            messagesEl.innerHTML = "";
            
            // Default welcome message if empty
            if (data.messages.length === 0) {
                messagesEl.innerHTML = `
                    <div class="chat-bubble chat-bubble-ai">
                        Halo! Saya Leli, asisten virtual budidaya ikan lele Anda. Ada yang bisa saya bantu hari ini?
                        <div class="chat-bubble-time">${new Date(data.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                `;
            }
            
            data.messages.forEach(msg => {
                const bubble = document.createElement("div");
                bubble.className = `chat-bubble chat-bubble-${msg.sender_type === "user" ? "user" : "ai"}`;
                
                // Parse newline to br for nicer rendering
                const formattedText = msg.message_text.replace(/\n/g, "<br>");
                
                bubble.innerHTML = `
                    ${formattedText}
                    <div class="chat-bubble-time">${new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                `;
                messagesEl.appendChild(bubble);
            });
            
            scrollChatToBottom();
            
            // Mark session as active in list UI
            const sessionsList = document.getElementById("chat-sessions-list");
            const items = sessionsList.querySelectorAll(".session-item");
            items.forEach((item, index) => {
                // Find matching item based on summary context click or order
            });
            loadChatSessionsListOnly();
        }
    } catch (e) {
        messagesEl.innerHTML = `<p style="color:var(--danger); text-align:center;">Gagal memuat pesan.</p>`;
    }
}

// Minimal function to reload session list without clearing messages
async function loadChatSessionsListOnly() {
    const listContainer = document.getElementById("chat-sessions-list");
    try {
        const response = await fetch(API_URLS.chatSessions, {
            headers: { "Authorization": `Bearer ${state.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const sessions = data.results || data;
            listContainer.innerHTML = "";
            
            sessions.forEach(session => {
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
    } catch (e) {}
}

async function sendMessage() {
    const messageInput = document.getElementById("chat-message-input");
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Clear input
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
    
    // Send to backend
    const payload = { message };
    if (state.activeSessionId) {
        payload.session_id = state.activeSessionId;
    }
    
    try {
        const response = await fetch(API_URLS.chat, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${state.token}`
            },
            body: JSON.stringify(payload)
        });
        
        // Remove typing indicator
        typingIndicator.remove();
        
        if (response.ok) {
            const data = await response.json();
            
            // Save active session
            state.activeSessionId = data.session_id;
            
            // Add AI bubble
            const aiBubble = document.createElement("div");
            aiBubble.className = "chat-bubble chat-bubble-ai";
            const formattedResponse = data.response.replace(/\n/g, "<br>");
            aiBubble.innerHTML = `
                ${formattedResponse}
                <div class="chat-bubble-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            `;
            messagesEl.appendChild(aiBubble);
            scrollChatToBottom();
            
            // Re-focus input so user can keep chatting
            messageInput.focus();
            
            // Refresh list
            loadChatSessionsListOnly();
        } else {
            showToast("Gagal menerima respons chatbot.", "error");
            messageInput.focus();
        }
    } catch (err) {
        typingIndicator.remove();
        showToast("Kesalahan koneksi ke chatbot.", "error");
        messageInput.focus();
    }
}

function scrollChatToBottom() {
    const messagesEl = document.getElementById("chat-messages-container");
    // Use requestAnimationFrame for reliable scroll after DOM update
    requestAnimationFrame(() => {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    });
}

/* ─────────────────────────────────────────────────────────────────────────
   KNOWLEDGE BASE & ARTICLES
   ───────────────────────────────────────────────────────────────────────── */
async function loadKnowledgeBase() {
    // Load diseases
    try {
        const resPenyakit = await fetch(API_URLS.penyakit);
        if (resPenyakit.ok) {
            const data = await resPenyakit.json();
            state.diseases = data.results || data;
            displayDiseases(state.diseases);
        }
    } catch (e) {
        console.error("Gagal memuat data penyakit:", e);
    }
    
    // Load articles
    try {
        const resArtikel = await fetch(API_URLS.artikel);
        if (resArtikel.ok) {
            const data = await resArtikel.json();
            state.articles = data.results || data;
            displayArticles(state.articles);
        }
    } catch (e) {
        console.error("Gagal memuat artikel edukasi:", e);
    }
}

function getDiseaseIcon(name) {
    const lowerName = name.toLowerCase();
    if (lowerName.includes("aeromonas")) return "🦠";     // Bakteri Aeromonas
    if (lowerName.includes("jamur")) return "🍄";         // Jamur/Fungi Saprolegnia
    if (lowerName.includes("malnutrisi")) return "🦴";   // Defisiensi gizi (kurus/tulang)
    if (lowerName.includes("overfeeding")) return "🎈";   // Kembung perut buncit (balon)
    return "🐟";
}

function displayDiseases(diseases) {
    const grid = document.getElementById("disease-directory-grid");
    if (!grid) return;
    
    grid.innerHTML = "";
    // Skip 'Sehat' class from showing in directory
    const actualDiseases = diseases.filter(d => d.nama !== "Sehat");
    
    actualDiseases.forEach(d => {
        const card = document.createElement("div");
        card.className = "glass-card disease-card";
        const icon = getDiseaseIcon(d.nama);
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
    
    // Medicine info
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
    
    // Close button
    modal.querySelector(".modal-close").onclick = () => {
        modal.classList.remove("active");
    };
    
    // Click outside to close
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
    
    // Populate content into symptoms section as block
    document.getElementById("modal-disease-symptoms").parentNode.style.display = "none";
    document.getElementById("modal-disease-cause").parentNode.style.display = "none";
    document.getElementById("modal-disease-prevention").parentNode.style.display = "none";
    document.getElementById("modal-disease-treatment").parentNode.style.display = "none";
    document.getElementById("modal-disease-medicines").parentNode.style.display = "none";
    
    // Put content in description block
    const formattedContent = a.konten.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    document.getElementById("modal-disease-desc").innerHTML = formattedContent;
    
    modal.classList.add("active");
    
    // Close button restore
    const cleanClose = () => {
        modal.classList.remove("active");
        // Restore display values
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
async function loadDetectionHistory() {
    const tableBody = document.getElementById("history-table-body");
    tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center;"><div class="loader-spinner" style="width:30px;height:30px;"></div></td></tr>`;
    
    try {
        const response = await fetch(API_URLS.history, {
            headers: { "Authorization": `Bearer ${state.token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const logs = data.results || data;
            tableBody.innerHTML = "";
            
            if (logs.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">Belum ada riwayat deteksi.</td></tr>`;
                return;
            }
            
            logs.forEach(log => {
                const tr = document.createElement("tr");
                const date = new Date(log.created_at).toLocaleDateString("id-ID", { dateStyle: "medium" });
                
                let statusBadge = "";
                if (log.status_proses === "done") {
                    statusBadge = `<span class="result-badge badge-sehat" style="padding:2px 8px;font-size:10px;">Selesai</span>`;
                } else if (log.status_proses === "processing") {
                    statusBadge = `<span class="result-badge badge-sakit" style="padding:2px 8px;font-size:10px;background:rgba(59,130,246,0.15);color:var(--info);border-color:var(--info);">Diproses</span>`;
                } else {
                    statusBadge = `<span class="result-badge badge-sakit" style="padding:2px 8px;font-size:10px;">Gagal</span>`;
                }
                
                tr.innerHTML = `
                    <td style="font-weight:600;">#${log.id}</td>
                    <td>${date}</td>
                    <td style="text-transform: capitalize;">${log.penyakit_terdeteksi.replace("_", " ") || "Pending"}</td>
                    <td>${log.confidence_persen}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-secondary btn-view-log" style="padding:6px 12px; font-size:11px; margin:0;">Detail</button>
                    </td>
                `;
                
                tr.querySelector(".btn-view-log").addEventListener("click", () => {
                    showSection("detection");
                    displayDetectionResult(log);
                    // Update preview image
                    const previewContainer = document.querySelector(".preview-container");
                    const previewImg = document.querySelector(".preview-img");
                    previewImg.src = log.image;
                    previewContainer.style.display = "block";
                    document.getElementById("btn-analyze-ai").style.display = "none";
                });
                
                tableBody.appendChild(tr);
            });
        }
    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--danger);">Gagal memuat riwayat.</td></tr>`;
    }
}
