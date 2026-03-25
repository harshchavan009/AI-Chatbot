const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const languageSelector = document.getElementById('language-selector');

// Check for authentication token
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login.html';
}

const username = localStorage.getItem('username') || 'User';

document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    window.location.href = '/login.html';
});

// Generate a random session ID for the browser session
const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);

function addMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    
    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.innerText = text;
    
    messageDiv.appendChild(bubble);
    chatWindow.appendChild(messageDiv);
    
    // Scroll to bottom
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('message', 'assistant', 'typing-indicator');
    
    const typing = document.createElement('div');
    typing.classList.add('typing');
    
    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        typing.appendChild(dot);
    }
    
    typingDiv.appendChild(typing);
    chatWindow.appendChild(typingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return typingDiv;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    // Add user message to UI
    addMessage(text, 'user');
    userInput.value = '';

    // Add typing indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                user_input: text,
                session_id: sessionId,
                language: languageSelector.value
            })
        });

        if (response.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
            return;
        }

        const data = await response.json();
        
        // Remove typing indicator
        typingIndicator.remove();

        if (data.response) {
            addMessage(data.response, 'assistant');
        } else {
            addMessage("I'm sorry, I couldn't process your request.", 'assistant');
        }
    } catch (error) {
        typingIndicator.remove();
        addMessage("Error connecting to server. Please try again later.", 'assistant');
        console.error('Error:', error);
    }
});
