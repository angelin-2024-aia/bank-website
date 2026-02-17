document.addEventListener('DOMContentLoaded', () => {
    // --- 1. LOGIN LOGIC ---
    const loginForm = document.getElementById('loginForm');
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            // Simple redirection logic for demo
            if (loginSection && dashboardSection) {
                loginSection.style.display = 'none';
                dashboardSection.style.display = 'block';
                console.log("Login Successful: Redirected to Dashboard");
            } else {
                // If on a separate login.html page, it will redirect to /
                window.location.href = '/';
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

        // User message-ai display pannu
        chatDisplay.innerHTML += `
            <div style="text-align:right; margin-bottom:12px;">
                <span style="background:#10b981; color:white; padding:8px 12px; border-radius:12px 12px 0 12px; display:inline-block; max-width:80%;">
                    ${question}
                </span>
            </div>`;
        
        inputField.value = "";
        
        // "Thinking" indicator create pannu
        const botId = "bot-" + Date.now();
        chatDisplay.innerHTML += `
            <div id="${botId}" style="text-align:left; margin-bottom:12px;">
                <span style="background:#e5e7eb; color:#1e293b; padding:8px 12px; border-radius:12px 12px 12px 0; display:inline-block;">
                    Thinking... 🤖
                </span>
            </div>`;
        
        chatDisplay.scrollTop = chatDisplay.scrollHeight;

        try {
            // Flask API-ku request anupu
            const response = await fetch('/api/rag-query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            
            // Bot reply-ai update pannu
            const botMsgSpan = document.getElementById(botId).querySelector('span');
            botMsgSpan.innerText = data.answer || "I'm sorry, I couldn't process that.";
            
        } catch (error) {
            console.error('Error:', error);
            const botMsgSpan = document.getElementById(botId).querySelector('span');
            botMsgSpan.innerText = "⚠️ Server Error. Please check your app.py.";
            botMsgSpan.style.color = "red";
        }

        chatDisplay.scrollTop = chatDisplay.scrollHeight;
    }

    // Event listeners for sending message
    if (sendBtn) {
        sendBtn.onclick = sendMessage;
    }

    if (inputField) {
        inputField.onkeypress = (e) => {
            if (e.key === 'Enter') sendMessage();
        };
    }
});