const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

function safeMarkdown(text) {
    return DOMPurify.sanitize(marked.parse(text || ''));
}

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    if (role === 'ai') {
        msgDiv.innerHTML = safeMarkdown(text);
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

function handleAuthError(response) {
    try {
        response.json().then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        });
    } catch (_) {
        window.location.href = '/login/';
    }
}

// Load conversation history on page load
async function loadHistory() {
    const module = (window.CHAT_MODULE || 'USB').toUpperCase();
    try {
        const resp = await fetch(`/api/history/?module=${module}`);
        if (!resp.ok) {
            if (resp.status === 401) {
                window.location.href = '/login/';
            }
            return;
        }
        const data = await resp.json();
        if (data.history && data.history.length > 0) {
            // Clear the default greeting if there's real history
            chatContainer.innerHTML = '';
            for (const msg of data.history) {
                appendMessage(msg.role === 'assistant' ? 'ai' : 'user', msg.content);
            }
        }
    } catch (_) {}
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
        const streamUrl = window.CHAT_STREAM_URL || '/api/chat/stream';
        const response = await fetch(streamUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        if (!response.ok) {
            if (response.status === 401) {
                handleAuthError(response);
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }

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
                        msgDiv.innerHTML = safeMarkdown(accumulated) + '<span class="streaming-cursor">▌</span>';
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    } else if (event.t === 'status') {
                        msgDiv.innerHTML = safeMarkdown(accumulated) +
                            `<p class="deploy-status"><em>${event.v}</em> <span class="streaming-cursor">▌</span></p>`;
                    } else if (event.t === 'done') {
                        msgDiv.innerHTML = safeMarkdown(accumulated);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    } else if (event.t === 'error') {
                        msgDiv.innerHTML = safeMarkdown(event.v || 'An error occurred.');
                    }
                } catch (_) {}
            }
        }

        if (msgDiv.innerHTML.includes('streaming-cursor')) {
            try {
                msgDiv.innerHTML = safeMarkdown(accumulated) || accumulated || 'No response.';
            } catch (_) {
                msgDiv.innerHTML = accumulated || 'No response.';
            }
        }

        if (accumulated.includes('Strategy Saved Successfully') && typeof window.loadStrategyCounts === 'function') {
            window.loadStrategyCounts();
        }

        if (typeof window.loadBalance === 'function') {
            window.loadBalance();
        }

    } catch (error) {
        console.error('[Chat stream error]', error);
        msgDiv.innerHTML = `Error: ${error.message || 'Could not connect to the backend.'}`;
    } finally {
        setInputLocked(false);
        userInput.focus();
    }
}

sendBtn.addEventListener('click', handleSend);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});

// Load history when the page is ready
document.addEventListener('DOMContentLoaded', loadHistory);
if (document.readyState !== 'loading') {
    loadHistory();
}
