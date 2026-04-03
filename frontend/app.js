// Endpoint URL relative to where the server runs. Adjust if deploying separately.
const API_URL = "http://127.0.0.1:5001/generate-reply";

const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

// State: Track conversation
let chatHistory = [];

/**
 * Utility to create a message bubble HTML element mapping nicely to standard semantic UI layout
 */
function appendMessage(role, messageText, isTyping = false) {
    const messageContainer = document.createElement("div");
    // 'consultant' maps to AI, 'client' maps to user
    messageContainer.className = `message ${role}`;
    
    // Create the bubble block
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    
    if (isTyping) {
        bubble.id = "typingIndicator";
        bubble.innerHTML = `
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
    } else {
        bubble.textContent = messageText;
    }
    
    messageContainer.appendChild(bubble);
    chatBox.appendChild(messageContainer);
    
    // Scroll to bottom smoothly
    chatBox.parentElement.scrollTop = chatBox.parentElement.scrollHeight;
}

function removeTypingIndicator() {
    const typing = document.getElementById("typingIndicator");
    if (typing) {
        typing.parentElement.remove();
    }
}

async function handleSendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    
    // Clear Input
    messageInput.value = "";
    messageInput.style.height = "auto"; // Reset auto-growth
    
    // Render the user message immediately
    appendMessage("client", text);
    
    // Render loading indicator
    appendMessage("consultant", "", true);
    
    // Disable send button while waiting
    sendBtn.disabled = true;
    
    try {
        // Send strictly the layout from `/generate-reply`
        const payload = {
            clientSequence: text,
            chatHistory: chatHistory
        };
        
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        removeTypingIndicator();
        
        if (response.ok && data.aiReply) {
            // Render the consultant's text
            appendMessage("consultant", data.aiReply);
            
            // Push interaction into memory so conversation has context growing forward
            chatHistory.push({ role: "client", message: text });
            chatHistory.push({ role: "consultant", message: data.aiReply });
        } else {
            console.error("Server Error:", data);
            appendMessage("consultant", "Sorry, I am facing an issue connecting to the visa network. Please try again later.");
        }
    } catch (err) {
        console.error("Network Error:", err);
        removeTypingIndicator();
        appendMessage("consultant", "Connection failed. Please ensure the backend is running and try again.");
    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

// Event Listeners
sendBtn.addEventListener("click", handleSendMessage);

messageInput.addEventListener("keydown", (e) => {
    // Submit on Enter (allow shift+enter for new lines)
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});

// Auto-resizing textarea
messageInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
});
