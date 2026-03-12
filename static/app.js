document.addEventListener('DOMContentLoaded', () => {

    // --- 1. LOGIN LOGIC WITH ML SECURITY CHECK ---
    const loginForm = document.getElementById('loginForm');
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');

    // MUKKIYAM: Madhu-voda Flask Server URL
    const MADHU_SERVER_IP = "http://172.16.125.155:8000"; 

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            console.log("Security Check: Contacting ML Engine...");

            try {
                // 🔥 CALL MADHU'S ML API BEFORE LOGIN
                const response = await fetch(`http://172.16.125.155:8000/classify`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        attack_type: "phishing"   // demo attack type
                    })
                });

                const data = await response.json();
                console.log("ML Result:", data);

                // 🚨 BLOCK AND REDIRECT IF ANOMALY DETECTED
                if (data.anomaly === "anomaly") {
                    alert("⚠️ SECURITY ALERT: Suspicious activity detected!");
                    document.body.style.backgroundColor = "#ffcccc"; 
                    
                    // --- REDIRECTION LOGIC ---
                    console.log("Redirecting Attacker to Fake Environment...");
                    window.location.href = "fake_dashboard.html"; // Attacker-ah inga anupuvom
                    return;
                }

            } catch (err) {
                console.error("ML API connection error:", err);
                alert("Security system is offline. Please try again later.");
                return;
            }

            // ✅ SAFE LOGIN FLOW - Only runs if ML says "Normal"
            if (loginSection && dashboardSection) {
                loginSection.style.display = 'none';
                dashboardSection.style.display = 'block';
                console.log("Login Successful: Redirected to Dashboard");
            } else {
                window.location.reload(); 
            }
        });
    }

    // --- 2. FLOATING CHATBOT UI TOGGLE ---
    const chatToggle = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const closeChat = document.getElementById('close-chat');

    if (chatToggle && chatWindow) {
        chatToggle.onclick = () => {
            const isHidden = chatWindow.style.display === 'none' || chatWindow.style.display === '';
            chatWindow.style.display = isHidden ? 'block' : 'none';
        };
    }

    if (closeChat) {
        closeChat.onclick = () => {
            chatWindow.style.display = 'none';
        };
    }

    // --- 3. AI CHATBOT RAG ENGINE LOGIC ---
    const sendBtn = document.getElementById('floating-send-btn');
    const inputField = document.getElementById('floating-question');
    const chatDisplay = document.getElementById('ai-answer-container');

    async function sendMessage() {
        const question = inputField.value.trim();
        if (!question) return;

        chatDisplay.innerHTML += `
            <div style="text-align:right; margin-bottom:12px;">
                <span style="background:#10b981; color:white; padding:8px 12px; border-radius:12px 12px 0 12px; display:inline-block; max-width:80%;">
                    ${question}
                </span>
            </div>`;

        inputField.value = "";

        const botId = "bot-" + Date.now();
        chatDisplay.innerHTML += `
            <div id="${botId}" style="text-align:left; margin-bottom:12px;">
                <span style="background:#e5e7eb; color:#1e293b; padding:8px 12px; border-radius:12px 12px 12px 0; display:inline-block;">
                    Thinking... 🤖
                </span>
            </div>`;

        chatDisplay.scrollTop = chatDisplay.scrollHeight;

        try {
            const response = await fetch(`${MADHU_SERVER_IP}/api/rag-query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            const botMsgSpan = document.getElementById(botId).querySelector('span');
            botMsgSpan.innerText = data.answer || "I'm sorry, I couldn't process that.";

        } catch (error) {
            console.error('Chatbot Error:', error);
            const botMsgSpan = document.getElementById(botId).querySelector('span');
            botMsgSpan.innerText = "⚠️ AI Server Error. Please check Madhu's Laptop.";
            botMsgSpan.style.color = "red";
        }

        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    if (sendBtn) { sendBtn.onclick = sendMessage; }
    if (inputField) {
        inputField.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
    }
});