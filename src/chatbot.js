// Chat Ternak Frontend JavaScript
// Author: Galuh Adi Insani

document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Add event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Add help button functionality
    const helpButton = document.getElementById('help-button');
    if (helpButton) {
        helpButton.addEventListener('click', showHelp);
    }

    // Function to send messages
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input
        userInput.value = '';

        // Show typing indicator
        addTypingIndicator();

        // Send to backend - either local API or DeepSeek API based on question complexity
        fetch('http://localhost:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add bot response to chat
            addMessageToChat('bot', data.response);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessageToChat('bot', 'Maaf, terjadi kesalahan saat berkomunikasi dengan server. Silakan coba lagi.');
        });
    }

    // Function to add message to chat
    function addMessageToChat(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(sender + '-message');
        
        // Process message for links and formatting
        const formattedMessage = formatMessage(message);
        
        messageElement.innerHTML = formattedMessage;
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Add typing indicator
    function addTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'bot-message', 'typing-indicator');
        typingElement.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
        typingElement.id = 'typing-indicator';
        chatMessages.appendChild(typingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove typing indicator
    function removeTypingIndicator() {
        const typingElement = document.getElementById('typing-indicator');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    // Format message to handle links and formatting
    function formatMessage(message) {
        // Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        message = message.replace(urlRegex, url => `<a href="${url}" target="_blank">${url}</a>`);
        
        // Convert newlines to <br>
        message = message.replace(/\n/g, '<br>');
        
        // Handle bullet points
        message = message.replace(/- (.*)/g, '<li>$1</li>');
        if (message.includes('<li>')) {
            message = `<ul>${message}</ul>`;
        }
        
        return `<p>${message}</p>`;
    }
});

// Add enhanced help functionality
function showHelp() {
    const helpContent = `
        <div class="help-content">
            <h2>Bantuan Penggunaan Chat Ternak</h2>
            
            <h3>🔍 Cara Menggunakan Chatbot:</h3>
            <p>Ketik pertanyaan Anda tentang peternakan dan pertanian di kotak chat, lalu tekan Enter atau klik tombol Kirim.</p>
            
            <h3>🐄 Topik yang Didukung:</h3>
            <ul>
                <li><strong>Informasi Ternak:</strong> Sapi, kambing, ayam, bebek, ikan, kelinci</li>
                <li><strong>Aspek Peternakan:</strong> Jenis, perawatan, pakan, reproduksi, penyakit, produksi</li>
                <li><strong>Pupuk Organik:</strong> Informasi tentang pengolahan kotoran ternak menjadi pupuk</li>
            </ul>
            
            <h3>📊 Fitur Analisis Data:</h3>
            <ul>
                <li><strong>Prediksi Pertumbuhan:</strong> Contoh: "Prediksi pertumbuhan sapi dari berat 250 kg dengan pertambahan 0.8 kg per hari selama 90 hari"</li>
                <li><strong>Perhitungan Kebutuhan Pakan:</strong> Contoh: "Hitung kebutuhan pakan untuk 5 ekor kambing dengan berat 35 kg"</li>
                <li><strong>Analisis BEP:</strong> Contoh: "Hitung BEP dengan biaya tetap 20 juta harga jual 50 ribu dan biaya variabel 30 ribu"</li>
            </ul>
            
            <h3>💡 Contoh Pertanyaan:</h3>
            <ul>
                <li>"Apa saja jenis sapi yang populer di Indonesia?"</li>
                <li>"Bagaimana cara merawat kambing?"</li>
                <li>"Berapa kebutuhan pakan untuk 10 ekor ayam?"</li>
                <li>"Jelaskan tentang reproduksi pada kelinci"</li>
                <li>"Bagaimana cara membuat pupuk dari kotoran ternak?"</li>
                <li>"Prediksi pertumbuhan ikan dengan berat 0.5 kg dengan pertambahan 0.05 kg per hari selama 30 hari"</li>
            </ul>
            
            <h3>🔄 Mode DeepSeek AI:</h3>
            <p>Untuk pertanyaan kompleks, Chat Ternak akan secara otomatis menggunakan AI canggih dari DeepSeek untuk memberikan jawaban yang lebih lengkap dan terperinci.</p>
            
            <div class="help-footer">
                <button id="close-help-btn" class="close-help-button">Tutup</button>
            </div>
        </div>
    `;
    
    // Create modal overlay
    const helpModal = document.createElement('div');
    helpModal.classList.add('help-modal');
    helpModal.innerHTML = helpContent;
    document.body.appendChild(helpModal);
    
    // Show with animation
    setTimeout(() => {
        helpModal.classList.add('active');
    }, 10);
    
    // Add event listener to close button
    document.getElementById('close-help-btn').addEventListener('click', () => {
        helpModal.classList.remove('active');
        setTimeout(() => {
            helpModal.remove();
        }, 300);
    });
}