const chatWindow = document.getElementById('chat-window');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const languageDropdown = document.getElementById('language-dropdown');
const selectedLangText = document.getElementById('selected-lang-text');
// Token is retrieved fresh from localStorage in each API call to avoid stale session issues

// API Helper
let API_BASE_URL = 'https://nova-ai-chatbot-8b04.onrender.com';
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    API_BASE_URL = ''; // Use relative paths for local development
} else if (window.location.hostname.includes('onrender.com')) {
    API_BASE_URL = ''; // Use relative paths if hosted directly on Render
}

function getApiUrl(path) {
    // Ensure we don't double slash
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${API_BASE_URL}${cleanPath}`;
}

// Session State
let currentSessionId = 'session_' + Math.random().toString(36).substr(2, 9);

// Sidebar Elements
const historyList = document.getElementById('history-list');
const newChatBtn = document.getElementById('new-chat-btn');
const usernameDisplay = document.getElementById('username-display');
const logoutBtnSidebar = document.getElementById('logout-btn-sidebar');
const userAvatarSidebar = document.getElementById('user-avatar-sidebar');

// Photo Sharing Elements
let selectedImageBase64 = null;
let selectedDocumentBase64 = null;
let selectedDocumentName = null;

// Photo Sharing Elements
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-input');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImageBtn = document.getElementById('remove-image');
const micBtn = document.getElementById('mic-btn');

// Avatars
const ASSISTANT_AVATAR = `<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><path d="M12 6v6l4 2"/></svg>`;
const USER_AVATAR = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

// Theme Elements
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const SUN_ICON = `<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>`;
const MOON_ICON = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>`;
let vantaEffect = null;

// Settings Elements
const settingsToggle = document.getElementById('settings-toggle');
const settingsModal = document.getElementById('settings-modal');
const closeSettings = document.getElementById('close-settings');
const saveSettings = document.getElementById('save-settings');
const modelSelect = document.getElementById('model-select');
const tempSlider = document.getElementById('temp-slider');
const tempValueDisplay = document.getElementById('temp-value');
const languageSelect = document.getElementById('language-select');

let aiSettings = {
    model: localStorage.getItem('ai_model') || 'gemini-2.5-flash',
    temperature: parseFloat(localStorage.getItem('ai_temp')) || 0.7,
    language: localStorage.getItem('ai_language') || 'Auto-detect'
};

// Initialize Vanta
function initVanta() {
    if (typeof VANTA === 'undefined') return;
    vantaEffect = VANTA.NET({
        el: "#vanta-canvas",
        mouseControls: true,
        touchControls: true,
        gyroControls: false,
        minHeight: 200.00,
        minWidth: 200.00,
        scale: 1.00,
        scaleMobile: 1.00,
        color: 0x6366f1,
        backgroundColor: 0x0f172a,
        points: 12.00,
        maxDistance: 22.00,
        spacing: 16.00
    });
}

// Global Language State
let selectedLanguage = localStorage.getItem('ai_language') || 'Auto-detect';

// Initialize Settings UI
function initSettingsUI() {
    if (!settingsToggle || !settingsModal) return;

    // Load initial values into UI
    modelSelect.value = aiSettings.model;
    tempSlider.value = aiSettings.temperature;
    tempValueDisplay.textContent = aiSettings.temperature;
    if (languageSelect) languageSelect.value = selectedLanguage;

    settingsToggle.addEventListener('click', () => {
        // Sync modal with global state before opening
        if (languageSelect) languageSelect.value = selectedLanguage;
        settingsModal.classList.remove('hidden');
    });

    closeSettings.addEventListener('click', () => {
        settingsModal.classList.add('hidden');
    });

    // Close on overlay click
    const overlay = settingsModal.querySelector('.modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', () => {
            settingsModal.classList.add('hidden');
        });
    }

    tempSlider.addEventListener('input', (e) => {
        tempValueDisplay.textContent = e.target.value;
    });

    saveSettings.addEventListener('click', () => {
        aiSettings.model = modelSelect.value;
        aiSettings.temperature = parseFloat(tempSlider.value);
        
        // Sync from modal to global
        if (languageSelect) {
            selectedLanguage = languageSelect.value;
            aiSettings.language = selectedLanguage;
            localStorage.setItem('ai_language', selectedLanguage);
            
            // Update header UI to match modal selection
            const options = languageDropdown.querySelectorAll('.option');
            const activeOption = Array.from(options).find(opt => opt.dataset.value === selectedLanguage);
            if (activeOption) selectedLangText.innerHTML = activeOption.innerHTML;
        }

        localStorage.setItem('ai_model', aiSettings.model);
        localStorage.setItem('ai_temp', aiSettings.temperature);
        settingsModal.classList.add('hidden');
        
        // Brief visual feedback
        const originalText = saveSettings.textContent;
        saveSettings.textContent = 'Saved! ✅';
        setTimeout(() => saveSettings.textContent = originalText, 2000);
    });
}

// Separate Language Dropdown Logic (Independent of Settings Modal presence)
function initLanguageSelector() {
    if (!languageDropdown) return;

    const dropdownSelected = languageDropdown.querySelector('.dropdown-selected');
    const options = languageDropdown.querySelectorAll('.option');
    const dropdownOptions = languageDropdown.querySelector('.dropdown-options');

    // Initial set from state
    const currentOption = Array.from(options).find(opt => opt.dataset.value === selectedLanguage);
    if (currentOption) selectedLangText.innerHTML = currentOption.innerHTML;

    dropdownSelected.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdownOptions.classList.toggle('show'); // Matches CSS .dropdown-options.show
    });

    options.forEach(option => {
        option.addEventListener('click', () => {
            selectedLanguage = option.dataset.value;
            selectedLangText.innerHTML = option.innerHTML;
            localStorage.setItem('ai_language', selectedLanguage);
            dropdownOptions.classList.remove('show');
            
            // Keep settings modal select in sync if it exists
            if (languageSelect) languageSelect.value = selectedLanguage;
            
            console.log(`Language changed to: ${selectedLanguage}`);
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        if (dropdownOptions) dropdownOptions.classList.remove('show');
    });
}

// Start core UI components
initSettingsUI();
initLanguageSelector();

// Voice Input Logic
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    
    recognition.onstart = () => {
        micBtn.classList.add('recording');
        userInput.placeholder = 'Listening...';
    };
    
    recognition.onend = () => {
        micBtn.classList.remove('recording');
        userInput.placeholder = 'Type your message...';
    };
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        micBtn.classList.remove('recording');
        userInput.placeholder = 'Type your message...';
    };
}

if (micBtn) {
    micBtn.onclick = () => {
        if (!recognition) {
            alert('Speech recognition is not supported in this browser.');
            return;
        }
        if (micBtn.classList.contains('recording')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    };
}

function setTheme(theme) {
    if (theme === 'light') {
        document.body.classList.add('light-theme');
        themeIcon.innerHTML = MOON_ICON;
        localStorage.setItem('theme', 'light');
        if (vantaEffect) vantaEffect.setOptions({ color: 0x4f46e5, backgroundColor: 0xf1f5f9 });
    } else {
        document.body.classList.remove('light-theme');
        themeIcon.innerHTML = SUN_ICON;
        localStorage.setItem('theme', 'dark');
        if (vantaEffect) vantaEffect.setOptions({ color: 0x6366f1, backgroundColor: 0x0f172a });
    }
}

// Check for authentication token - consolidated at top of file
const currentToken = localStorage.getItem('access_token');
if (!currentToken) {
    window.location.href = '/login.html';
}

const username = localStorage.getItem('username') || 'User';

// Sidebar footer logout button handled in main event listener below

// Sidebar and History Logic
async function loadConversations() {
    const freshToken = localStorage.getItem('access_token');
    if (!freshToken) {
        historyList.innerHTML = '<div class="empty-history">Log in to see history</div>';
        return;
    }

    try {
        // Add a timeout for the fetch to handle Render cold starts
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(getApiUrl('/api/conversations'), {
            headers: { 'Authorization': `Bearer ${freshToken}` },
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/login.html';
                return;
            }
            throw new Error('API Error');
        }
        
        const conversations = await response.json();
        renderHistoryList(conversations);
    } catch (error) {
        console.error('Error loading conversations:', error);
        if (error.name === 'AbortError') {
            historyList.innerHTML = '<div class="error">Server is waking up... Please wait.</div>';
            // Retry after 5 seconds
            setTimeout(loadConversations, 5000);
        } else {
            historyList.innerHTML = '<div class="error">Failed to load history</div>';
        }
    }
}

function renderHistoryList(conversations) {
    if (conversations.length === 0) {
        historyList.innerHTML = '<div class="empty-history">No recent chats</div>';
        return;
    }

    historyList.innerHTML = conversations.map(chat => `
        <div class="history-item ${chat.id === currentSessionId ? 'active' : ''}" data-id="${chat.id}">
            <div class="history-content" onclick="switchConversation('${chat.id}')">
                <span class="history-name">${chat.title}</span>
                <span class="history-msg">${chat.last_message}</span>
            </div>
            <div class="history-actions">
                <button class="action-btn rename-btn" onclick="promptRename('${chat.id}', '${chat.title}')" title="Rename">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                </button>
                <button class="action-btn delete-btn" onclick="deleteConversation('${chat.id}')" title="Delete">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                </button>
            </div>
        </div>
    `).join('');
}

async function switchConversation(id) {
    if (id === currentSessionId) return;
    currentSessionId = id;
    
    // UI update
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-id') === id);
    });

    // ... (rest of switchConversation logic)
    const dashboard = document.querySelector('.dashboard-onboarding');
    if (dashboard) dashboard.style.display = 'none';
    
    chatWindow.innerHTML = '<div class="history-loading">Loading messages...</div>';

    try {
        const freshToken = localStorage.getItem('access_token');
        const response = await fetch(getApiUrl(`/api/conversations/${id}`), {
            headers: { 'Authorization': `Bearer ${freshToken}` }
        });
        const data = await response.json();
        chatWindow.innerHTML = '';
        data.messages.forEach(msg => {
            addMessage(msg.content, msg.role);
        });
        chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (error) {
        console.error('Error switching conversation:', error);
        chatWindow.innerHTML = '<div class="error">Failed to load conversation</div>';
    }
}

function startNewChat() {
    currentSessionId = 'session_' + Math.random().toString(36).substr(2, 9);
    chatWindow.innerHTML = '';
    // Re-inject dashboard if it was removed
    if (!document.querySelector('.dashboard-onboarding')) {
        location.reload(); // Simplest way to restore empty state for now
    }
    
    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
}

async function promptRename(id, oldTitle) {
    const newTitle = prompt('Enter new title for this chat:', oldTitle);
    if (!newTitle || newTitle === oldTitle) return;

    try {
        const freshToken = localStorage.getItem('access_token');
        await fetch(getApiUrl(`/api/conversations/${id}`), {
            method: 'PATCH',
            headers: { 
                'Authorization': `Bearer ${freshToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: newTitle })
        });
        loadConversations();
    } catch (error) {
        alert('Failed to rename conversation');
    }
}

async function deleteConversation(id) {
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    try {
        const freshToken = localStorage.getItem('access_token');
        await fetch(getApiUrl(`/api/conversations/${id}`), {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${freshToken}` }
        });
        if (id === currentSessionId) {
            startNewChat();
        }
        loadConversations();
    } catch (error) {
        alert('Failed to delete conversation');
    }
}

// Connection Status Logic
const connStatusBadge = document.getElementById('conn-status');
const connStatusText = connStatusBadge.querySelector('.status-text');

async function updateConnectionStatus() {
    if (!navigator.onLine) {
        connStatusBadge.classList.add('reconnecting');
        connStatusText.innerText = 'Offline ❌';
        return;
    }

    try {
        const res = await fetch(getApiUrl('/health'), { cache: 'no-store' });
        if (res.ok) {
            connStatusBadge.classList.remove('reconnecting');
            connStatusText.innerText = 'Connected ✅';
        } else {
            connStatusBadge.classList.add('reconnecting');
            connStatusText.innerText = 'Server Error ⚠️';
        }
    } catch (e) {
        connStatusBadge.classList.add('reconnecting');
        connStatusText.innerText = 'Waking Server... ⏳';
    }
}

// Check connection every 30 seconds
setTimeout(() => {
    updateConnectionStatus();
    setInterval(updateConnectionStatus, 30000);
}, 2000);

window.addEventListener('online', updateConnectionStatus);
window.addEventListener('offline', updateConnectionStatus);

// Move all initialization into a single safe DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        initVanta();
        const savedTheme = localStorage.getItem('theme') || 'dark';
        setTheme(savedTheme);
        
        if (localStorage.getItem('access_token')) {
            const username = localStorage.getItem('username') || 'User';
            if (usernameDisplay) usernameDisplay.innerText = username;
            if (userAvatarSidebar) userAvatarSidebar.innerText = username[0].toUpperCase();
            loadConversations();
        }
    } catch (e) {
        console.error('Initialization error:', e);
    }
});

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const isLight = document.body.classList.contains('light-theme');
        setTheme(isLight ? 'dark' : 'light');
    });
}

newChatBtn.addEventListener('click', startNewChat);

logoutBtnSidebar.addEventListener('click', () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    window.location.href = 'login.html';
});

// Photo Sharing Logic
/* State handled above */

uploadBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        const base64String = event.target.result;
        
        // Reset previous selections
        selectedImageBase64 = null;
        selectedDocumentBase64 = null;
        selectedDocumentName = null;

        if (file.type.startsWith('image/')) {
            selectedImageBase64 = base64String;
            imagePreview.src = base64String;
            imagePreview.style.display = 'block';
            
            // Remove any old doc preview if it existed
            const oldDocPreview = document.getElementById('doc-icon-preview');
            if (oldDocPreview) oldDocPreview.remove();
            
            const oldFileInfo = document.querySelector('.file-info');
            if (oldFileInfo) oldFileInfo.remove();
            
        } else if (file.type === 'application/pdf' || file.type === 'text/plain') {
            selectedDocumentBase64 = base64String;
            selectedDocumentName = file.name;
            
            imagePreview.style.display = 'none';
            
            // Create or update document preview
            let docPreview = document.getElementById('doc-icon-preview');
            if (!docPreview) {
                docPreview = document.createElement('div');
                docPreview.id = 'doc-icon-preview';
                docPreview.className = 'doc-icon-preview';
                imagePreviewContainer.insertBefore(docPreview, removeImageBtn);
            }
            docPreview.textContent = file.type === 'application/pdf' ? 'PDF' : 'TXT';
            
            let fileInfo = document.querySelector('.file-info');
            if (!fileInfo) {
                fileInfo = document.createElement('div');
                fileInfo.className = 'file-info';
                imagePreviewContainer.insertBefore(fileInfo, removeImageBtn);
            }
            fileInfo.innerHTML = `
                <span class="file-name">${file.name}</span>
                <span class="file-type">${file.type === 'application/pdf' ? 'PDF Document' : 'Text File'}</span>
            `;
        }

        imagePreviewContainer.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
});

removeImageBtn.addEventListener('click', () => {
    selectedImageBase64 = null;
    selectedDocumentBase64 = null;
    selectedDocumentName = null;
    fileInput.value = '';
    imagePreviewContainer.classList.add('hidden');
    imagePreview.src = '';
    
    // Cleanup dynamic elements
    const docPreview = document.getElementById('doc-icon-preview');
    if (docPreview) docPreview.remove();
    const fileInfo = document.querySelector('.file-info');
    if (fileInfo) fileInfo.remove();
});

// Onboarding Dashboard Logic
const onboardingDashboard = document.getElementById('onboarding-dashboard');

function hideOnboarding() {
    if (onboardingDashboard && !onboardingDashboard.classList.contains('hidden')) {
        onboardingDashboard.style.display = 'none';
        onboardingDashboard.classList.add('hidden');
    }
}

document.querySelectorAll('.quick-action-card').forEach(card => {
    card.addEventListener('click', () => {
        const query = card.getAttribute('data-query');
        userInput.value = query;
        chatForm.dispatchEvent(new Event('submit'));
    });
});

// Interactive Capability Cards
document.querySelectorAll('.capability-item').forEach(card => {
    card.addEventListener('click', () => {
        const action = card.getAttribute('data-action');
        if (action === 'analyze-image' || action === 'upload-doc') {
            fileInput.click();
        } else if (action === 'real-time-search') {
            userInput.value = "Search the web for: ";
            userInput.focus();
        } else if (action === 'smart-reasoning') {
            userInput.value = "Help me solve: ";
            userInput.focus();
        }
    });
});

function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function addMessage(text, role, imageUrl = null, documentName = null) {
    const wrapper = document.createElement('div');
    wrapper.classList.add('message-wrapper', role);
    
    // Avatar
    const avatar = document.createElement('div');
    avatar.classList.add('avatar');
    avatar.innerHTML = role === 'assistant' ? ASSISTANT_AVATAR : USER_AVATAR;
    
    // Content Container
    const content = document.createElement('div');
    content.classList.add('message-content');
    
    // Bubble
    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    
    if (text) {
        const textElement = document.createElement('div');
        textElement.innerText = text;
        bubble.appendChild(textElement);
    }
    
    if (imageUrl) {
        const imgContainer = document.createElement('div');
        imgContainer.classList.add('image-container');
        const img = document.createElement('img');
        img.src = imageUrl;
        img.classList.add('message-image');
        img.alt = "Shared image";
        imgContainer.appendChild(img);
        bubble.appendChild(imgContainer);
    }

    if (documentName) {
        const docContainer = document.createElement('div');
        docContainer.classList.add('message-document');
        docContainer.innerHTML = `
            <div class="message-doc-icon">📄</div>
            <div class="message-doc-info">
                <span class="message-doc-name">${documentName}</span>
                <span class="message-doc-type">Document</span>
            </div>
        `;
        bubble.appendChild(docContainer);
    }
    
    // Timestamp
    const timestamp = document.createElement('span');
    timestamp.classList.add('timestamp');
    timestamp.innerText = getFormattedTime();
    
    content.appendChild(bubble);
    content.appendChild(timestamp);
    
    wrapper.appendChild(avatar);
    wrapper.appendChild(content);
    
    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return bubble;
}

function updateMessageImage(bubble, imageUrl) {
    // Check if image container already exists
    if (bubble.querySelector('.image-container')) return;
    
    const imgContainer = document.createElement('div');
    imgContainer.classList.add('image-container');
    
    const loader = document.createElement('div');
    loader.classList.add('image-loading-spinner');
    imgContainer.appendChild(loader);

    const img = document.createElement('img');
    img.src = imageUrl;
    img.classList.add('message-image');
    img.alt = "Related image";
    img.onload = () => {
        loader.remove();
    };
    img.onerror = () => {
        imgContainer.remove();
    };

    imgContainer.appendChild(img);
    bubble.appendChild(imgContainer);
}

function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('message-wrapper', 'assistant', 'typing-indicator');
    
    const container = document.createElement('div');
    container.classList.add('typing-container');

    const spinner = document.createElement('div');
    spinner.classList.add('image-loading-spinner'); // Reuse existing spinner style
    spinner.style.width = '18px';
    spinner.style.height = '18px';
    spinner.style.borderWidth = '2px';
    
    const text = document.createElement('span');
    text.classList.add('thinking-text');
    text.innerText = 'AI is thinking...';

    container.appendChild(spinner);
    container.appendChild(text);
    typingDiv.appendChild(container);
    chatWindow.appendChild(typingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return typingDiv;
}

function showError(message, retryCallback) {
    const bubble = addMessage("", 'assistant');
    bubble.classList.add('error-bubble');
    
    const header = document.createElement('div');
    header.classList.add('error-header');
    header.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>Oops! ${message}</span>
    `;
    
    const retryBtn = document.createElement('button');
    retryBtn.classList.add('retry-btn');
    retryBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        Retry Request
    `;
    
    retryBtn.onclick = () => {
        bubble.closest('.message-wrapper').remove();
        retryCallback();
    };
    
    bubble.appendChild(header);
    bubble.appendChild(retryBtn);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text && !selectedImageBase64) return;

    hideOnboarding();

    // Add user message to UI
    addMessage(text, 'user', selectedImageBase64, selectedDocumentName);
    
    const currentImage = selectedImageBase64;
    const currentDoc = selectedDocumentBase64;
    const currentDocName = selectedDocumentName;
    
    // Clear input and preview
    userInput.value = '';
    selectedImageBase64 = null;
    selectedDocumentBase64 = null;
    selectedDocumentName = null;
    fileInput.value = '';
    imagePreviewContainer.classList.add('hidden');
    
    // Cleanup dynamic preview elements
    const docPreviewNode = document.getElementById('doc-icon-preview');
    if (docPreviewNode) docPreviewNode.remove();
    const fileInfoNode = document.querySelector('.file-info');
    if (fileInfoNode) fileInfoNode.remove();

    // Add typing indicator
    const typingIndicator = addTypingIndicator();
    
    // Set loading state on send button
    const sendBtn = chatForm.querySelector('.send-btn');
    if (sendBtn) sendBtn.classList.add('loading');

    try {
        const fetchResponse = async () => {
            const freshToken = localStorage.getItem('access_token');
            const response = await fetch(getApiUrl('/api/chat/stream'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${freshToken}`
                },
                body: JSON.stringify({
                    user_input: text || (currentImage ? "What is in this image?" : (currentDoc ? "Analyze this document." : "")),
                    session_id: currentSessionId,
                    language: selectedLanguage,
                    image: currentImage,
                    document: currentDoc,
                    document_name: currentDocName,
                    model: aiSettings.model,
                    temperature: aiSettings.temperature
                })
            });

            if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/login.html';
                return;
            }

            if (response.status === 429) {
                throw new Error('Our AI models are hitting their usage limits. Please wait a few seconds and try again.');
            }

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantBubble = null;
            let fullText = "";
            let typingIndicatorRemoved = false;

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.type === 'text') {
                                if (!typingIndicatorRemoved) {
                                    typingIndicator.remove();
                                    typingIndicatorRemoved = true;
                                }
                                if (!assistantBubble) {
                                    assistantBubble = addMessage("", 'assistant');
                                }
                                // Use a dedicated text element to avoid clearing images
                                let textEl = assistantBubble.querySelector('.message-text');
                                if (!textEl) {
                                    textEl = document.createElement('div');
                                    textEl.classList.add('message-text');
                                    assistantBubble.prepend(textEl);
                                }
                                fullText += data.chunk;
                                textEl.innerText = fullText;
                                chatWindow.scrollTop = chatWindow.scrollHeight;
                            } else if (data.type === 'image' && data.url) {
                                if (!typingIndicatorRemoved) {
                                    typingIndicator.remove();
                                    typingIndicatorRemoved = true;
                                }
                                if (!assistantBubble) {
                                    assistantBubble = addMessage("", 'assistant');
                                }
                                updateMessageImage(assistantBubble, data.url);
                            } else if (data.type === 'metadata') {
                                console.log('Stream Metadata:', data);
                                currentSessionId = data.session_id;
                                loadConversations();
                            }
                        } catch (e) {
                            console.error('Error parsing stream chunk:', e, line);
                        }
                    }
                }
            }
        };

        await fetchResponse();
    } catch (error) {
        if (typingIndicator) typingIndicator.remove();
        showError("Server is taking too long.", () => {
            // Re-inject typing indicator and retry
            const newIndicator = addTypingIndicator();
            // Re-run the same logic (this is a bit recursive, but clean for a quick retry)
            chatForm.dispatchEvent(new Event('submit'));
        });
        console.error('Error:', error);
    } finally {
        // Remove loading state from send button
        const sendBtn = chatForm.querySelector('.send-btn');
        if (sendBtn) sendBtn.classList.remove('loading');
    }
});

// --- Mobile Responsiveness Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    if (mobileToggle && sidebar && sidebarOverlay) {
        const toggleSidebar = () => {
            sidebar.classList.toggle('active');
            sidebarOverlay.classList.toggle('active');
        };

        mobileToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar();
        });

        sidebarOverlay.addEventListener('click', toggleSidebar);

        // Close sidebar when clicking a chat session or new chat on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
                if (e.target.closest('.history-item') || 
                    e.target.closest('.new-chat-btn') || 
                    e.target.closest('#logout-btn-sidebar')) {
                    sidebar.classList.remove('active');
                    sidebarOverlay.classList.remove('active');
                }
            }
        });
    }
});
