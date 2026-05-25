const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    
    if (role === 'ai') {
        msgDiv.innerHTML = marked.parse(text);
    } else {
        msgDiv.textContent = text;
    }
    
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';

    // Typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message';
    typingDiv.textContent = 'AI is thinking...';
    chatContainer.appendChild(typingDiv);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: 'user_1' })
        });
        const data = await response.json();
        
        chatContainer.removeChild(typingDiv);
        appendMessage('ai', data.message);
    } catch (error) {
        chatContainer.removeChild(typingDiv);
        appendMessage('ai', 'Error: Could not connect to the backend.');
    }
}

sendBtn.addEventListener('click', handleSend);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});
