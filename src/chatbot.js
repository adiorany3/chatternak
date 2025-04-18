// Farming Chat Bot Logic
document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Knowledge base for farming topics
    const farmingKnowledge = {
        // Ternak Sapi (Cattle)
        'sapi': {
            'info': 'Sapi adalah hewan ternak yang umum dibudidayakan untuk daging, susu, dan tenaga kerja. Di Indonesia, beberapa jenis sapi yang populer adalah sapi Bali, sapi Madura, dan sapi PO (Peranakan Ongole).',
            'perawatan': 'Perawatan sapi meliputi pemberian pakan berkualitas (hijauan dan konsentrat), kandang yang bersih, vaksinasi rutin, dan pemeriksaan kesehatan.',
            'pakan': 'Pakan sapi terdiri dari hijauan (rumput gajah, rumput raja) dan konsentrat (dedak, ampas tahu, bungkil kelapa). Sapi dewasa membutuhkan sekitar 10% dari berat badannya untuk pakan hijauan per hari.',
            'reproduksi': 'Masa kebuntingan sapi sekitar 9 bulan. Deteksi birahi penting untuk keberhasilan perkawinan. Sapi dapat dikawinkan secara alami atau dengan Inseminasi Buatan (IB).',
        },
        
        // Ternak Kambing (Goats)
        'kambing': {
            'info': 'Kambing adalah ternak yang mudah dipelihara dan memiliki nilai ekonomi tinggi. Jenis kambing di Indonesia antara lain kambing Kacang, kambing Etawa, dan kambing Jawarandu.',
            'perawatan': 'Kambing membutuhkan kandang yang kering dan bersih, pakan yang cukup, dan perawatan kuku secara berkala. Kambing juga perlu divaksin terhadap penyakit seperti tetanus dan enterotoksemia.',
            'pakan': 'Kambing adalah ruminansia yang memakan berbagai jenis daun-daunan, rumput, dan leguminosa. Pakan tambahan seperti ampas tahu dan dedak bisa diberikan untuk meningkatkan produktivitas.',
            'reproduksi': 'Masa kebuntingan kambing sekitar 5 bulan. Kambing betina dapat melahirkan 1-3 anak per kelahiran dan dapat beranak hingga 2 kali dalam setahun dengan manajemen yang baik.',
        },
        
        // Ternak Ayam (Chickens)
        'ayam': {
            'info': 'Peternakan ayam di Indonesia meliputi ayam pedaging (broiler), ayam petelur, dan ayam kampung. Ayam adalah ternak yang relatif mudah dibudidayakan dengan siklus produksi yang cepat.',
            'perawatan': 'Perawatan ayam meliputi kandang yang bersih dan nyaman, vaksinasi rutin, biosecurity ketat, dan manajemen pakan yang baik.',
            'pakan': 'Pakan ayam harus mengandung protein, energi, vitamin, dan mineral yang cukup. Ayam pedaging dan petelur membutuhkan formulasi pakan yang berbeda sesuai kebutuhan produksi.',
            'penyakit': 'Penyakit umum pada ayam antara lain Avian Influenza (flu burung), Newcastle Disease (ND), Infectious Bursal Disease (Gumboro), dan Chronic Respiratory Disease (CRD).',
        },
        
        // Ternak Bebek (Ducks)
        'bebek': {
            'info': 'Bebek (itik) populer dibudidayakan untuk daging dan telur. Jenis bebek yang umum di Indonesia adalah bebek Peking, bebek Alabio, dan itik Mojosari.',
            'perawatan': 'Bebek membutuhkan kandang yang cukup luas dengan akses ke air untuk berenang (opsional namun dianjurkan). Pemberian pakan teratur dan vaksinasi rutin diperlukan.',
            'pakan': 'Pakan bebek dapat berupa campuran dedak, bekatul, jagung giling, dan sumber protein seperti tepung ikan. Bebek juga menyukai sayuran hijau dan siput.',
            'produksi': 'Bebek petelur dapat menghasilkan 250-300 telur per tahun dengan manajemen yang baik. Bebek pedaging dapat dipanen pada umur 8-10 minggu.',
        },
        
        // Ternak Ikan (Fish)
        'ikan': {
            'info': 'Budidaya ikan air tawar populer di Indonesia, meliputi ikan lele, nila, gurame, mas, dan patin. Budidaya ikan dapat dilakukan di kolam tanah, terpal, atau sistem bioflok.',
            'kolam': 'Kolam ikan harus memiliki sumber air yang cukup dan berkualitas baik. Kedalaman kolam yang ideal adalah 1-1,5 meter dengan sistem aerasi yang baik.',
            'pakan': 'Pakan ikan bisa berupa pelet komersial atau pakan alami seperti cacing, dedak, dan ampas tahu. Pemberian pakan sebaiknya 2-3 kali sehari secara teratur.',
            'penyakit': 'Penyakit umum pada ikan antara lain white spot (bintik putih), dropsy (perut bengkak), dan jamur. Pencegahan melalui kualitas air yang baik dan tidak overstocking sangat penting.',
        },
        
        // Pupuk Organik (Organic Fertilizer)
        'pupuk': {
            'info': 'Kotoran ternak dapat diolah menjadi pupuk organik yang berkualitas untuk pertanian. Pupuk organik memperbaiki struktur tanah dan menambah nutrisi.',
            'kompos': 'Pengomposan adalah proses mengubah bahan organik menjadi pupuk dengan bantuan mikroorganisme. Bahan yang bisa dikomposkan meliputi kotoran ternak, sisa pakan, dan material organik lainnya.',
            'biogas': 'Kotoran ternak dapat diproses dalam digester biogas untuk menghasilkan gas metana sebagai energi alternatif dan sludge sebagai pupuk organik berkualitas.',
            'aplikasi': 'Pupuk organik sebaiknya diaplikasikan 2-3 minggu sebelum tanam dengan dosis 5-10 ton/hektar untuk hasil optimal.',
        }
    };

    // API URL for Python backend
    const API_URL = 'http://localhost:5000';

    // Function to add message to chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
        
        const messagePara = document.createElement('p');
        messagePara.textContent = message;
        
        messageDiv.appendChild(messagePara);
        chatMessages.appendChild(messageDiv);
        
        // Auto scroll to the bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to get bot response from Python backend
    async function getBotResponseFromPython(userMessage) {
        try {
            const response = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error fetching response from Python backend:', error);
            // Fallback to JavaScript logic if Python server is not available
            return getBotResponseFromJS(userMessage);
        }
    }

    // Original JavaScript response function (as fallback)
    function getBotResponseFromJS(userMessage) {
        userMessage = userMessage.toLowerCase();
        
        // Check for greetings
        if (userMessage.includes('halo') || userMessage.includes('hai') || userMessage.includes('hello')) {
            return 'Halo! Ada yang bisa saya bantu tentang peternakan?';
        }
        
        // Check for thanks
        if (userMessage.includes('terima kasih') || userMessage.includes('makasih')) {
            return 'Sama-sama! Ada pertanyaan lain tentang peternakan?';
        }
        
        // Check for specific farm animals or topics
        for (const topic in farmingKnowledge) {
            if (userMessage.includes(topic)) {
                // Check for specific aspects about the topic
                if (userMessage.includes('info') || userMessage.includes('tentang')) {
                    return farmingKnowledge[topic].info;
                } else if (userMessage.includes('perawatan') || userMessage.includes('merawat')) {
                    return farmingKnowledge[topic].perawatan || 'Maaf, informasi spesifik tentang perawatan ' + topic + ' belum tersedia.';
                } else if (userMessage.includes('pakan') || userMessage.includes('makan')) {
                    return farmingKnowledge[topic].pakan || 'Maaf, informasi tentang pakan ' + topic + ' belum tersedia.';
                } else if (userMessage.includes('reproduksi') || userMessage.includes('beranak') || userMessage.includes('kawin')) {
                    return farmingKnowledge[topic].reproduksi || 'Maaf, informasi tentang reproduksi ' + topic + ' belum tersedia.';
                } else if (userMessage.includes('penyakit') || userMessage.includes('sakit')) {
                    return farmingKnowledge[topic].penyakit || 'Maaf, informasi tentang penyakit ' + topic + ' belum tersedia.';
                } else if (userMessage.includes('produksi') || userMessage.includes('hasil')) {
                    return farmingKnowledge[topic].produksi || 'Maaf, informasi tentang produksi ' + topic + ' belum tersedia.';
                } else {
                    // Return general info if no specific aspect mentioned
                    return farmingKnowledge[topic].info;
                }
            }
        }
        
        // General questions about farming
        if (userMessage.includes('pupuk organik') || userMessage.includes('kompos')) {
            return farmingKnowledge.pupuk.kompos;
        } else if (userMessage.includes('biogas')) {
            return farmingKnowledge.pupuk.biogas;
        } else if (userMessage.includes('mulai beternak') || userMessage.includes('memulai peternakan')) {
            return 'Untuk memulai beternak, Anda perlu mempertimbangkan: 1) Jenis ternak yang sesuai dengan kondisi lingkungan dan pasar, 2) Modal yang tersedia, 3) Ketersediaan pakan, 4) Pengetahuan tentang manajemen ternak, dan 5) Perizinan yang diperlukan. Ternak pemula yang disarankan adalah ayam, kambing, atau ikan lele.';
        } else if (userMessage.includes('modal') || userMessage.includes('biaya')) {
            return 'Modal untuk memulai peternakan bervariasi tergantung jenis dan skala. Untuk skala kecil: Ayam petelur (50-100 ekor) sekitar Rp 5-10 juta, Kambing (5-10 ekor) sekitar Rp 10-20 juta, Ikan lele (1 kolam) sekitar Rp 3-5 juta. Modal tersebut mencakup bibit, kandang/kolam, dan pakan awal.';
        }
        
        // Default response if no matching answer found
        return 'Maaf, saya belum memiliki informasi spesifik tentang pertanyaan tersebut. Silakan tanyakan tentang peternakan sapi, kambing, ayam, bebek, ikan, atau pupuk organik.';
    }

    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send message on enter key
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    async function sendMessage() {
        const message = userInput.value.trim();
        
        if (message !== '') {
            // Add user message to chat
            addMessage(message, true);
            
            // Clear input field
            userInput.value = '';
            
            // Show loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.classList.add('message', 'bot-message', 'loading');
            loadingDiv.textContent = 'Memproses...';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            try {
                // Get bot response from Python backend
                const botResponse = await getBotResponseFromPython(message);
                
                // Remove loading indicator
                chatMessages.removeChild(loadingDiv);
                
                // Add bot response
                addMessage(botResponse);
            } catch (error) {
                // Remove loading indicator
                chatMessages.removeChild(loadingDiv);
                
                // Add error message
                addMessage('Maaf, terjadi kesalahan dalam memproses pesan Anda. Silakan coba lagi.');
                console.error(error);
            }
        }
    }

    // Function to analyze data
    async function analyzeData(dataType, values) {
        try {
            const response = await fetch(`${API_URL}/api/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ type: dataType, values: values }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            return data.result;
        } catch (error) {
            console.error('Error analyzing data:', error);
            return 'Maaf, terjadi kesalahan dalam menganalisis data.';
        }
    }

    // Add to global scope for potential use in console or other parts
    window.farmingChatbot = {
        analyzeData
    };
});