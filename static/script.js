// DOM Elements - Tabs
const generalTabBtn = document.getElementById('general-tab-btn');
const bookingTabBtn = document.getElementById('booking-tab-btn');
const generalTab = document.getElementById('general-tab');
const bookingTab = document.getElementById('booking-tab');

// DOM Elements - General Inquiry
const generalChatMessages = document.getElementById('generalChatMessages');
const generalInquiryInput = document.getElementById('generalInquiryInput');
const generalSendButton = document.getElementById('generalSendButton');
const generalTypingIndicator = document.getElementById('generalTypingIndicator');

// DOM Elements - Booking
const bookingIdSection = document.getElementById('bookingIdSection');
const bookingChatSection = document.getElementById('bookingChatSection');
const bookingIdInput = document.getElementById('bookingIdInput');
const verifyButton = document.getElementById('verifyButton');
const bookingChatMessages = document.getElementById('bookingChatMessages');
const bookingTypingIndicator = document.getElementById('bookingTypingIndicator');

// Add welcome message to general inquiry chat
addMessage(generalChatMessages, 'assistant', 'Welcome to our general inquiry service! How can I help you today?');

// Tab switching functionality
generalTabBtn.addEventListener('click', function() {
    setActiveTab(generalTabBtn, generalTab);
});

bookingTabBtn.addEventListener('click', function() {
    setActiveTab(bookingTabBtn, bookingTab);
});

function setActiveTab(activeButton, activeTab) {
    // Remove 'active' class from all tabs and contents
    generalTabBtn.classList.remove('active');
    bookingTabBtn.classList.remove('active');
    generalTab.classList.remove('active');
    bookingTab.classList.remove('active');

    // Add 'active' class to selected tab and content
    activeButton.classList.add('active');
    activeTab.classList.add('active');
}

// Function to add a message to chat
function addMessage(chatContainer, sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.textContent = message;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// General Inquiry - Send Message
generalSendButton.addEventListener('click', function() {
    sendMessage(generalChatMessages, generalInquiryInput, generalTypingIndicator);
});

// Booking Inquiry - Send Message
document.getElementById('bookingSendButton').addEventListener('click', function() {
    sendMessage(bookingChatMessages, document.getElementById('bookingInquiryInput'), bookingTypingIndicator);
});

// Function to handle sending messages
function sendMessage(chatContainer, inputField, typingIndicator) {
    const message = inputField.value.trim();
    if (message) {
        addMessage(chatContainer, 'user', message);
        inputField.value = '';

        // Show typing indicator briefly before response
        typingIndicator.style.display = 'flex';
        setTimeout(() => {
            typingIndicator.style.display = 'none';
            addMessage(chatContainer, 'assistant', 'Thank you for your message! We will get back to you shortly.');
        }, 1000);
    }
}

// Booking ID Verification
verifyButton.addEventListener('click', function() {
    const bookingId = bookingIdInput.value.trim();
    if (bookingId.match(/^BK\d{5}$/)) {
        document.getElementById('displayBookingId').textContent = bookingId;
        bookingIdSection.style.display = 'none';
        bookingChatSection.style.display = 'block';
    } else {
        document.getElementById('errorMessage').style.display = 'block';
    }
});
