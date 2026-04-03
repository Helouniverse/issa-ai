// We use a relative path now since Flask is serving this frontend natively!
const API_URL = "/generate-reply";

const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

// State
let chatHistory = [];
let messageCount = 0;
let currentPromptId = null;

// Modal Elements
const modal = document.getElementById("ratingModal");
const stars = document.querySelectorAll(".stars span");
const commentContainer = document.getElementById("commentContainer");
const submitCommentBtn = document.getElementById("submitCommentBtn");
const feedbackComment = document.getElementById("feedbackComment");
const modalTitle = document.getElementById("modalTitle");
const modalDesc = document.getElementById("modalDesc");
const closeModalBtn = document.getElementById("closeModalBtn");

function appendMessage(role, messageText, isTyping = false) {
    const messageContainer = document.createElement("div");
    messageContainer.className = `message ${role}`;
    
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
    chatBox.parentElement.scrollTop = chatBox.parentElement.scrollHeight;
}

function removeTypingIndicator() {
    const typing = document.getElementById("typingIndicator");
    if (typing) typing.parentElement.remove();
}

// ------ MODAL LOGIC ------
function showModal() {
    modal.classList.remove("hidden");
}

function hideModal() {
    modal.classList.add("hidden");
    // Reset modal state
    setTimeout(() => {
        stars.forEach(s => s.classList.remove("active"));
        commentContainer.classList.add("hidden");
        modalTitle.textContent = "How is my advice?";
        modalDesc.textContent = "Please rate your AI assistant experience.";
    }, 300);
}

closeModalBtn.addEventListener("click", hideModal);

stars.forEach((star, index) => {
    star.addEventListener("click", async () => {
        // Light up stars
        stars.forEach((s, i) => {
            if (i <= index) s.classList.add("active");
            else s.classList.remove("active");
        });
        
        const rating = index + 1;
        
        // Submit rating to API
        try {
            const res = await fetch("/submit-rating", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ promptId: currentPromptId, rating: rating })
            });
            const data = await res.json();
            
            if (data.isHighest === false) {
                // The AI degraded! Ask for a comment to auto-improve it.
                modalTitle.textContent = "Oh no, let's fix this.";
                modalDesc.textContent = `Score dropped to ${data.newScore.toFixed(1)}. Tell the AI exactly how to improve its behavior.`;
                commentContainer.classList.remove("hidden");
            } else {
                modalTitle.textContent = "Thank you!";
                modalDesc.textContent = "Your feedback keeps the AI smart.";
                setTimeout(hideModal, 1500);
            }
        } catch (err) {
            console.error(err);
        }
    });
});

submitCommentBtn.addEventListener("click", async () => {
    const comment = feedbackComment.value.trim();
    if (!comment) return;
    
    submitCommentBtn.textContent = "Teaching AI...";
    submitCommentBtn.disabled = true;
    
    try {
        const res = await fetch("/submit-comment", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ comment: comment, chatHistory: chatHistory })
        });
        const data = await res.json();
        
        if (data.success) {
            modalTitle.textContent = "Prompt Upgraded!";
            modalDesc.textContent = "The AI has generated a new logic rule based on your feedback and saved it to the database.";
            commentContainer.classList.add("hidden");
            setTimeout(hideModal, 2500);
        }
    } catch (err) {
        console.error(err);
    } finally {
        submitCommentBtn.textContent = "Teach AI";
        submitCommentBtn.disabled = false;
        feedbackComment.value = "";
    }
});
// -------------------------

async function handleSendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    
    messageInput.value = "";
    messageInput.style.height = "auto";
    
    appendMessage("client", text);
    appendMessage("consultant", "", true);
    sendBtn.disabled = true;
    
    try {
        const payload = {
            clientSequence: text,
            chatHistory: chatHistory
        };
        
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        removeTypingIndicator();
        
        if (response.ok && data.aiReply) {
            appendMessage("consultant", data.aiReply);
            
            // Save context
            chatHistory.push({ role: "client", message: text });
            chatHistory.push({ role: "consultant", message: data.aiReply });
            
            // Track Prompt ID
            if (data.promptId) {
                currentPromptId = data.promptId;
            }
            
            // Check for Rating Popup Trigger
            messageCount++;
            if (messageCount === 3) {
                showModal();
            }
            
        } else {
            appendMessage("consultant", "Sorry, I am facing an issue connecting to the visa network.");
        }
    } catch (err) {
        removeTypingIndicator();
        appendMessage("consultant", "Connection failed. Please ensure the backend is running and try again.");
    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

sendBtn.addEventListener("click", handleSendMessage);

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});

messageInput.addEventListener("input", function() {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight) + "px";
});
