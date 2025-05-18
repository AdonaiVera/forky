/**
 * Forky Chat Functionality
 * Handles the chat UI interaction and communication with the backend
 */

// Add a message to the chat UI
function addMessageToChat(role, content, format = null) {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'animate-fade-in';
    const timestamp = new Date().toLocaleTimeString();

    // Format the content if it's markdown
    const formattedContent = format === 'markdown'
        ? marked.parse(content) // Use marked.js to parse markdown
        : `<p class="text-sm text-gray-900">${escapeHTML(content)}</p>`;

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="flex items-start gap-2.5 flex-row-reverse">
                <div class="w-8 h-8 rounded-full bg-gray-100 border-2 border-gray-900 flex items-center justify-center text-gray-900 font-bold">
                    U
                </div>
                <div class="flex flex-col gap-1 w-full max-w-[320px]">
                    <div class="flex items-center space-x-2 flex-row-reverse">
                        <span class="text-sm font-semibold text-gray-900">You</span>
                        <span class="text-sm text-gray-500">${timestamp}</span>
                    </div>
                    <div class="flex flex-col leading-1.5 p-4 border-[2px] border-gray-900 bg-gray-100 rounded-s-xl rounded-ee-xl">
                        ${formattedContent}
                    </div>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="flex items-start gap-2.5">
                <div class="w-8 h-8 rounded-full bg-gradient-to-r from-[#4ECDC4] to-[#FF6B6B] flex items-center justify-center text-white font-bold">
                    AI
                </div>
                <div class="flex flex-col gap-1 w-full max-w-[80%]">
                    <div class="flex items-center space-x-2">
                        <span class="text-sm font-semibold text-gray-900">Forky</span>
                        <span class="text-sm text-gray-500">${timestamp}</span>
                    </div>
                    <div class="flex flex-col leading-1.5 p-4 border-[2px] border-gray-900 bg-[#4ECDC4]/10 rounded-e-xl rounded-es-xl overflow-hidden">
                        <div class="prose prose-sm max-w-full overflow-x-auto">
                            ${formattedContent}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Send a message to the backend
function sendChatMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);

    // Create FormData
    const formData = new FormData();
    formData.append('message', message);

    // Add repository context - using the direct summary and content from the analysis
    const summary = document.querySelector('[data-summary]')?.textContent;
    const content = document.querySelector('[data-content]')?.textContent;

    if (summary) formData.append('repo_summary', summary);
    if (content) formData.append('repo_content', content);

    // Show loading indicator
    const loadingIndicator = document.getElementById('chat-loading');
    if (loadingIndicator) loadingIndicator.classList.remove('hidden');

    // Clear input
    input.value = '';

    // Send to backend with timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    fetch('/chat', {
        method: 'POST',
        body: formData,
        signal: controller.signal
    })
    .then(response => {
        clearTimeout(timeoutId);
        if (!response.ok) {
            const errorMessage = response.status === 429
                ? 'Rate limit exceeded. Please try again in a moment.'
                : 'Network response was not ok';
            throw new Error(errorMessage);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) throw new Error(data.error);
        addMessageToChat('assistant', data.response, data.format);
    })
    .catch(error => {
        console.error('Error:', error);
        let errorMessage = 'Sorry, there was an error processing your request.';

        if (error.name === 'AbortError') {
            errorMessage = 'The request took too long to process. Please try again or simplify your query.';
        } else if (error.message) {
            errorMessage = `Error: ${error.message}`;
        }

        addMessageToChat('assistant', errorMessage);
    })
    .finally(() => {
        // Hide loading indicator
        if (loadingIndicator) loadingIndicator.classList.add('hidden');
    });
}

// Helper function to escape HTML to prevent XSS
function escapeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize chat functionality when document is ready
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('chat-input');
    const sendButton = document.getElementById('chat-send-button');

    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendChatMessage();
        });
    }
});
