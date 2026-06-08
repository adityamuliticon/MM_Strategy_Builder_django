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
    return msgDiv;
}

function setInputLocked(locked) {
    sendBtn.disabled = locked;
    userInput.disabled = locked;
}

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    userInput.value = '';
    setInputLocked(true);

    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai-message';
    msgDiv.innerHTML = '<em class="thinking-msg">Market Maya is thinking...</em> <span class="streaming-cursor">▌</span>';
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    let accumulated = '';

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: 'user_1' })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop();

            for (const part of parts) {
                if (!part.startsWith('data: ')) continue;
                try {
                    const event = JSON.parse(part.slice(6));

                    if (event.t === 'chunk') {
                        accumulated += event.v;
                        msgDiv.innerHTML = marked.parse(accumulated) + '<span class="streaming-cursor">▌</span>';
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    } else if (event.t === 'status') {
                        msgDiv.innerHTML = marked.parse(accumulated) +
                            `<p class="deploy-status"><em>${event.v}</em> <span class="streaming-cursor">▌</span></p>`;
                    } else if (event.t === 'done') {
                        msgDiv.innerHTML = marked.parse(accumulated);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    } else if (event.t === 'error') {
                        msgDiv.innerHTML = marked.parse(event.v || 'An error occurred.');
                    }
                } catch (_) {}
            }
        }

        // Safety: remove cursor if stream closed without a done event
        if (msgDiv.innerHTML.includes('streaming-cursor')) {
            msgDiv.innerHTML = marked.parse(accumulated) || 'No response.';
        }

        if (accumulated.includes('Strategy Saved Successfully') && typeof window.loadStrategyCounts === 'function') {
            window.loadStrategyCounts();
        }

        if (typeof window.loadBalance === 'function') {
            window.loadBalance();
        }

    } catch (error) {
        msgDiv.innerHTML = 'Error: Could not connect to the backend.';
    } finally {
        setInputLocked(false);
        userInput.focus();
    }
}

sendBtn.addEventListener('click', handleSend);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});
