import streamlit as st
import re
import random
import json
import os
import numpy as np
from datetime import datetime
import nltk
from nltk.stem import WordNetLemmatizer

# Download NLTK data - ensuring the required packages are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Page configuration
st.set_page_config(
    page_title="Chatternak - Farming Chat Bot",
    page_icon="🐄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Inisialisasi lemmatizer
lemmatizer = WordNetLemmatizer()

# Basis pengetahuan peternakan
farming_knowledge = {
    # Ternak Sapi (Cattle)
    'sapi': {
        'info': 'Sapi adalah hewan ternak yang umum dibudidayakan untuk daging, susu, dan tenaga kerja. Di Indonesia, beberapa jenis sapi yang populer adalah sapi Bali, sapi Madura, dan sapi PO (Peranakan Ongole).',
        'perawatan': 'Perawatan sapi meliputi pemberian pakan berkualitas (hijauan dan konsentrat), kandang yang bersih, vaksinasi rutin, dan pemeriksaan kesehatan.',
        'pakan': 'Pakan sapi terdiri dari hijauan (rumput gajah, rumput raja) dan konsentrat (dedak, ampas tahu, bungkil kelapa). Sapi dewasa membutuhkan sekitar 10% dari berat badannya untuk pakan hijauan per hari.',
        'reproduksi': 'Masa kebuntingan sapi sekitar 9 bulan. Deteksi birahi penting untuk keberhasilan perkawinan. Sapi dapat dikawinkan secara alami atau dengan Inseminasi Buatan (IB).',
        'jenis': 'Jenis sapi yang populer di Indonesia antara lain: Sapi Bali (asli Indonesia, tahan penyakit), Sapi PO/Peranakan Ongole (sapi pedaging unggul), Sapi Limosin (sapi impor dengan pertumbuhan cepat), Sapi Simental (produktivitas daging tinggi), dan Sapi FH/Friesian Holstein (penghasil susu).'
    },
    
    # Ternak Kambing (Goats)
    'kambing': {
        'info': 'Kambing adalah ternak yang mudah dipelihara dan memiliki nilai ekonomi tinggi. Jenis kambing di Indonesia antara lain kambing Kacang, kambing Etawa, dan kambing Jawarandu.',
        'perawatan': 'Kambing membutuhkan kandang yang kering dan bersih, pakan yang cukup, dan perawatan kuku secara berkala. Kambing juga perlu divaksin terhadap penyakit seperti tetanus dan enterotoksemia.',
        'pakan': 'Kambing adalah ruminansia yang memakan berbagai jenis daun-daunan, rumput, dan leguminosa. Pakan tambahan seperti ampas tahu dan dedak bisa diberikan untuk meningkatkan produktivitas.',
        'reproduksi': 'Masa kebuntingan kambing sekitar 5 bulan. Kambing betina dapat melahirkan 1-3 anak per kelahiran dan dapat beranak hingga 2 kali dalam setahun dengan manajemen yang baik.',
        'jenis': 'Jenis kambing yang populer di Indonesia adalah: Kambing Kacang (asli Indonesia, ukuran kecil), Kambing Etawa/PE (penghasil susu), Kambing Jawarandu (persilangan etawa dan kacang), Kambing Boer (kambing pedaging), dan Kambing Kosta (kambing dwiguna).'
    },
    
    # Ternak Ayam (Chickens)
    'ayam': {
        'info': 'Peternakan ayam di Indonesia meliputi ayam pedaging (broiler), ayam petelur, dan ayam kampung. Ayam adalah ternak yang relatif mudah dibudidayakan dengan siklus produksi yang cepat.',
        'perawatan': 'Perawatan ayam meliputi kandang yang bersih dan nyaman, vaksinasi rutin, biosecurity ketat, dan manajemen pakan yang baik.',
        'pakan': 'Pakan ayam harus mengandung protein, energi, vitamin, dan mineral yang cukup. Ayam pedaging dan petelur membutuhkan formulasi pakan yang berbeda sesuai kebutuhan produksi.',
        'penyakit': 'Penyakit umum pada ayam antara lain Avian Influenza (flu burung), Newcastle Disease (ND), Infectious Bursal Disease (Gumboro), dan Chronic Respiratory Disease (CRD).',
        'jenis': 'Jenis ayam yang umum diternakkan di Indonesia adalah: Ayam Broiler (pedaging, panen umur 35-40 hari), Ayam Layer (petelur, produksi hingga 300 telur/tahun), Ayam Kampung (asli Indonesia, pertumbuhan lambat), Ayam Jawa Super (hasil persilangan ayam kampung), dan Ayam Bangkok (ayam aduan).'
    },
    
    # Ternak Bebek (Ducks)
    'bebek': {
        'info': 'Bebek (itik) populer dibudidayakan untuk daging dan telur. Jenis bebek yang umum di Indonesia adalah bebek Peking, bebek Alabio, dan itik Mojosari.',
        'perawatan': 'Bebek membutuhkan kandang yang cukup luas dengan akses ke air untuk berenang (opsional namun dianjurkan). Pemberian pakan teratur dan vaksinasi rutin diperlukan.',
        'pakan': 'Pakan bebek dapat berupa campuran dedak, bekatul, jagung giling, dan sumber protein seperti tepung ikan. Bebek juga menyukai sayuran hijau dan siput.',
        'produksi': 'Bebek petelur dapat menghasilkan 250-300 telur per tahun dengan manajemen yang baik. Bebek pedaging dapat dipanen pada umur 8-10 minggu.',
        'jenis': 'Jenis bebek yang populer di Indonesia adalah: Bebek Peking (bebek pedaging), Itik Mojosari (petelur produktif), Itik Alabio (dwiguna, daging dan telur), Itik Bali/Itik Betutu (khas Bali), dan Itik Manila/Entok (ukuran besar).'
    },
    
    # Ternak Ikan (Fish)
    'ikan': {
        'info': 'Budidaya ikan air tawar populer di Indonesia, meliputi ikan lele, nila, gurame, mas, dan patin. Budidaya ikan dapat dilakukan di kolam tanah, terpal, atau sistem bioflok.',
        'kolam': 'Kolam ikan harus memiliki sumber air yang cukup dan berkualitas baik. Kedalaman kolam yang ideal adalah 1-1,5 meter dengan sistem aerasi yang baik.',
        'pakan': 'Pakan ikan bisa berupa pelet komersial atau pakan alami seperti cacing, dedak, dan ampas tahu. Pemberian pakan sebaiknya 2-3 kali sehari secara teratur.',
        'penyakit': 'Penyakit umum pada ikan antara lain white spot (bintik putih), dropsy (perut bengkak), dan jamur. Pencegahan melalui kualitas air yang baik dan tidak overstocking sangat penting.',
        'jenis': 'Jenis ikan air tawar yang umum dibudidayakan di Indonesia: Lele (tahan kondisi air buruk), Nila (pertumbuhan cepat), Gurame (nilai jual tinggi), Patin (produktivitas tinggi), dan Mas (mudah beradaptasi).'
    },
    
    # Pupuk Organik (Organic Fertilizer)
    'pupuk': {
        'info': 'Kotoran ternak dapat diolah menjadi pupuk organik yang berkualitas untuk pertanian. Pupuk organik memperbaiki struktur tanah dan menambah nutrisi.',
        'kompos': 'Pengomposan adalah proses mengubah bahan organik menjadi pupuk dengan bantuan mikroorganisme. Bahan yang bisa dikomposkan meliputi kotoran ternak, sisa pakan, dan material organik lainnya.',
        'biogas': 'Kotoran ternak dapat diproses dalam digester biogas untuk menghasilkan gas metana sebagai energi alternatif dan sludge sebagai pupuk organik berkualitas.',
        'aplikasi': 'Pupuk organik sebaiknya diaplikasikan 2-3 minggu sebelum tanam dengan dosis 5-10 ton/hektar untuk hasil optimal.',
        'jenis': 'Jenis pupuk organik dari peternakan: Pupuk kandang (langsung dari kotoran ternak), Kompos (hasil dekomposisi bahan organik), Kascing (kotoran cacing), Pupuk hijau (dari tanaman yang dibenamkan), dan Bio-slurry (hasil sampingan biogas).'
    },
    
    # Data tambahan: Kelinci
    'kelinci': {
        'info': 'Kelinci adalah hewan ternak yang mudah dibudidayakan dengan siklus reproduksi cepat dan efisiensi pakan yang tinggi.',
        'perawatan': 'Perawatan kelinci meliputi kandang yang bersih dan kering, area yang teduh, vaksinasi, dan pemeriksaan kuku secara berkala.',
        'pakan': 'Kelinci memakan berbagai jenis sayuran, rumput, dan pelet khusus kelinci. Kelinci dewasa mengkonsumsi sekitar 5-7% dari berat badannya per hari.',
        'reproduksi': 'Kelinci betina dapat melahirkan 4-12 anak setiap kelahiran dengan masa kebuntingan sekitar 30-32 hari. Kelinci dapat berkembang biak mulai umur 5-6 bulan.',
        'jenis': 'Jenis kelinci yang populer di Indonesia: New Zealand White (daging), Rex (bulu dan daging), Angora (bulu), Flemish Giant (ukuran besar), dan Lop (hias).'
    }
}

# Dataset untuk pertanyaan dan intents
intents = {
    "greeting": {
        "patterns": ["halo", "hai", "hello", "selamat pagi", "selamat siang", "selamat malam"],
        "responses": [
            "Halo! Ada yang bisa saya bantu tentang peternakan?",
            "Hai! Mau tanya apa tentang peternakan?",
            "Selamat datang! Saya siap menjawab pertanyaan Anda tentang peternakan."
        ]
    },
    "thanks": {
        "patterns": ["terima kasih", "makasih", "thank you", "thanks", "tq"],
        "responses": [
            "Sama-sama! Ada pertanyaan lain tentang peternakan?",
            "Senang bisa membantu. Ada hal lain yang ingin ditanyakan?",
            "Dengan senang hati. Semoga informasinya bermanfaat!"
        ]
    },
    "bye": {
        "patterns": ["bye", "sampai jumpa", "selamat tinggal", "dadah", "sudah cukup"],
        "responses": [
            "Sampai jumpa lagi!",
            "Terima kasih telah bertanya. Sampai jumpa!",
            "Silakan kembali jika ada pertanyaan lain. Selamat tinggal!"
        ]
    },
    "fallback": {
        "patterns": [],
        "responses": [
            "Maaf, saya belum memiliki informasi spesifik tentang pertanyaan tersebut. Silakan tanyakan tentang peternakan sapi, kambing, ayam, bebek, ikan, kelinci, atau pupuk organik.",
            "Pertanyaan Anda di luar pengetahuan saya saat ini. Coba tanyakan tentang jenis hewan ternak, cara perawatan, pakan, atau reproduksi hewan ternak.",
            "Saya tidak memiliki jawaban untuk pertanyaan itu. Saya lebih fasih menjawab tentang topik peternakan dan pertanian."
        ]
    },
    "modal_peternakan": {
        "patterns": ["modal", "biaya", "investasi", "berapa modal", "biaya awal", "uang"],
        "responses": [
            "Modal untuk memulai peternakan bervariasi tergantung jenis dan skala. Untuk skala kecil: Ayam petelur (50-100 ekor) sekitar Rp 5-10 juta, Kambing (5-10 ekor) sekitar Rp 10-20 juta, Ikan lele (1 kolam) sekitar Rp 3-5 juta. Modal tersebut mencakup bibit, kandang/kolam, dan pakan awal."
        ]
    },
    "mulai_beternak": {
        "patterns": ["mulai beternak", "memulai peternakan", "awal beternak", "pemula", "bagaimana memulai"],
        "responses": [
            "Untuk memulai beternak, Anda perlu mempertimbangkan: 1) Jenis ternak yang sesuai dengan kondisi lingkungan dan pasar, 2) Modal yang tersedia, 3) Ketersediaan pakan, 4) Pengetahuan tentang manajemen ternak, dan 5) Perizinan yang diperlukan. Ternak pemula yang disarankan adalah ayam, kambing, atau ikan lele."
        ]
    },
    "cuaca": {
        "patterns": ["cuaca", "musim", "hujan", "kemarau", "suhu", "iklim"],
        "responses": [
            "Cuaca sangat memengaruhi manajemen peternakan. Pada musim hujan, pastikan kandang tidak bocor dan memiliki drainase yang baik. Pada musim kemarau, siapkan cadangan air dan hindari kandang yang terlalu panas. Ternak yang berbeda memiliki toleransi suhu optimal yang berbeda."
        ]
    },
    "analisis_data": {
        "patterns": ["analisis", "data", "statistik", "prediksi", "perhitungan"],
        "responses": [
            "Saya dapat membantu menganalisis data peternakan dengan Python. Beberapa contoh analisis yang dapat dilakukan adalah: prediksi produksi, analisis pertumbuhan ternak, perhitungan efisiensi pakan, dan optimasi biaya produksi."
        ]
    }
}

# Preprocessing data
words = []
classes = []
documents = []
ignore_words = ['?', '!', '.', ',']

# Membuat dataset training
for intent in intents:
    for pattern in intents[intent]["patterns"]:
        # Tokenize setiap kata dalam kalimat
        w = nltk.word_tokenize(pattern)
        # Tambahkan ke daftar kata
        words.extend(w)
        # Tambahkan ke dokumen
        documents.append((w, intent))
        # Tambahkan ke daftar kelas
        if intent not in classes:
            classes.append(intent)

# Lemmatize dan filter kata-kata yang duplikat
words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

# Fungsi untuk analisis data sederhana dengan numpy
def analyze_data(data_type, values):
    """Analisis data sederhana menggunakan numpy"""
    try:
        values = np.array(values, dtype=float)
        result = {
            'mean': np.mean(values).round(2),
            'median': np.median(values).round(2),
            'std_dev': np.std(values).round(2),
            'min': np.min(values).round(2),
            'max': np.max(values).round(2)
        }
        return f"Analisis data {data_type}:\nRata-rata: {result['mean']}\nMedian: {result['median']}\nStandar Deviasi: {result['std_dev']}\nMinimum: {result['min']}\nMaksimum: {result['max']}"
    except Exception as e:
        return f"Gagal menganalisis data: {str(e)}"

# Fungsi untuk prediksi pertumbuhan ternak sederhana
def predict_growth(initial_weight, daily_gain, days):
    """Prediksi pertumbuhan ternak sederhana"""
    try:
        daily_gain = float(daily_gain)
        days = int(days)
        initial_weight = float(initial_weight)
        
        weights = [initial_weight + (daily_gain * day) for day in range(days + 1)]
        final_weight = weights[-1]
        
        return {
            'initial_weight': initial_weight,
            'final_weight': final_weight,
            'weight_gain': final_weight - initial_weight,
            'days': days,
            'weights': weights
        }
    except Exception as e:
        return {'error': str(e)}

# Fungsi untuk hitung kebutuhan pakan
def calculate_feed_needs(animal_type, count, avg_weight=None):
    """Hitung kebutuhan pakan berdasarkan jenis dan jumlah ternak"""
    feed_rates = {
        'sapi': 0.03,  # 3% dari berat badan
        'kambing': 0.04,  # 4% dari berat badan
        'ayam': 0.1,  # 10% dari berat badan
        'bebek': 0.08,  # 8% dari berat badan
        'ikan': 0.05,  # 5% dari berat badan
        'kelinci': 0.07  # 7% dari berat badan
    }
    
    default_weights = {
        'sapi': 400,  # kg
        'kambing': 40,  # kg
        'ayam': 2,  # kg
        'bebek': 3,  # kg
        'ikan': 0.5,  # kg
        'kelinci': 4  # kg
    }
    
    try:
        animal_type = animal_type.lower()
        count = int(count)
        if avg_weight is None:
            avg_weight = default_weights.get(animal_type, 1)
        else:
            avg_weight = float(avg_weight)
        
        if animal_type not in feed_rates:
            return f"Jenis ternak '{animal_type}' tidak dikenali."
        
        daily_feed_per_animal = avg_weight * feed_rates[animal_type]
        total_daily_feed = daily_feed_per_animal * count
        monthly_feed = total_daily_feed * 30
        
        return f"Untuk {count} ekor {animal_type} dengan berat rata-rata {avg_weight} kg:\n" \
               f"- Kebutuhan pakan per hari per ekor: {daily_feed_per_animal:.2f} kg\n" \
               f"- Total kebutuhan pakan harian: {total_daily_feed:.2f} kg\n" \
               f"- Perkiraan kebutuhan pakan bulanan: {monthly_feed:.2f} kg"
    except Exception as e:
        return f"Gagal menghitung kebutuhan pakan: {str(e)}"

# Fungsi untuk menghitung Break Even Point (BEP) sederhana
def calculate_bep(fixed_cost, price_per_unit, variable_cost_per_unit):
    """Hitung titik impas (BEP) sederhana"""
    try:
        fixed_cost = float(fixed_cost)
        price_per_unit = float(price_per_unit)
        variable_cost_per_unit = float(variable_cost_per_unit)
        
        if price_per_unit == variable_cost_per_unit:
            return "Harga jual sama dengan biaya variabel, BEP tidak dapat dihitung."
        
        bep_units = fixed_cost / (price_per_unit - variable_cost_per_unit)
        bep_revenue = bep_units * price_per_unit
        
        return f"Analisis BEP (Break Even Point):\n" \
               f"- Jumlah unit pada titik impas: {bep_units:.2f} unit\n" \
               f"- Pendapatan pada titik impas: Rp {bep_revenue:,.2f}\n" \
               f"- Artinya Anda perlu menjual minimal {bep_units:.2f} unit untuk tidak rugi."
    except Exception as e:
        return f"Gagal menghitung BEP: {str(e)}"

# Fungsi untuk memperoleh respons bot
def get_bot_response(message):
    message = message.lower()
    
    # Cek pola pertanyaan dengan Python processing
    # Cek greeting, thanks, bye
    for intent in ['greeting', 'thanks', 'bye']:
        for pattern in intents[intent]["patterns"]:
            if pattern in message:
                return random.choice(intents[intent]["responses"])
    
    # Cek permintaan untuk analisis data
    if any(kw in message for kw in ["analisis", "analisa", "hitung", "kalkulasi", "prediksi"]):
        # Analisis pertumbuhan ternak
        growth_match = re.search(r'prediksi\s+(?:pertumbuhan|berat)\s+(\w+)\s+(?:dari|dengan|berat)\s+(\d+(?:\.\d+)?)\s+(?:kg|kilogram)?\s+(?:dengan|dan)\s+(?:pertambahan|kenaikan)\s+(\d+(?:\.\d+)?)\s+(?:kg|kilogram)?\s+(?:per|setiap|tiap)\s+(?:hari|harian)\s+(?:selama|untuk)\s+(\d+)\s+(?:hari|hari)', message)
        if growth_match:
            animal, init_weight, daily_gain, days = growth_match.groups()
            result = predict_growth(init_weight, daily_gain, days)
            if 'error' in result:
                return f"Maaf, terjadi kesalahan: {result['error']}"
            return f"Prediksi pertumbuhan {animal}:\n" \
                   f"- Berat awal: {result['initial_weight']} kg\n" \
                   f"- Berat akhir setelah {result['days']} hari: {result['final_weight']:.2f} kg\n" \
                   f"- Total pertambahan berat: {result['weight_gain']:.2f} kg"
        
        # Analisis kebutuhan pakan
        feed_match = re.search(r'(?:hitung|berapa)\s+(?:kebutuhan|jumlah)\s+pakan\s+(?:untuk|bagi)\s+(\d+)\s+(?:ekor|benih|bibit)\s+(\w+)(?:\s+dengan\s+berat\s+(\d+(?:\.\d+)?)\s+(?:kg|kilogram))?', message)
        if feed_match:
            count, animal_type, weight = feed_match.groups()
            return calculate_feed_needs(animal_type, count, weight)
        
        # Analisis BEP
        bep_match = re.search(r'(?:hitung|berapa)\s+(?:bep|break\s+even\s+point|titik\s+impas)\s+(?:dengan|untuk)\s+(?:biaya\s+tetap|modal\s+tetap)\s+(\d+(?:\.\d+)?)\s+(?:juta|ribu|rp)?\s+(?:harga\s+jual|harga)\s+(\d+(?:\.\d+)?)\s+(?:ribu|rp)?\s+(?:dan|dengan)\s+(?:biaya\s+variabel|biaya\s+per\s+unit)\s+(\d+(?:\.\d+)?)', message)
        if bep_match:
            fixed_cost, price, variable_cost = bep_match.groups()
            # Konversi ke nilai numerik jika ada kata "juta" atau "ribu"
            if "juta" in message:
                fixed_cost = float(fixed_cost) * 1000000
            elif "ribu" in message:
                fixed_cost = float(fixed_cost) * 1000
            else:
                fixed_cost = float(fixed_cost)
                
            return calculate_bep(fixed_cost, float(price), float(variable_cost))
        
        # Jika permintaan analisis tidak spesifik
        return "Saya dapat melakukan analisis data peternakan seperti prediksi pertumbuhan, perhitungan kebutuhan pakan, dan analisis BEP. Mohon berikan detail yang lebih spesifik."
    
    # Cek pertanyaan tentang hewan ternak atau topik lain
    for topic in farming_knowledge:
        if topic in message:
            # Cek untuk aspek spesifik tentang topik
            if 'jenis' in message or 'tipe' in message or 'macam' in message or 'populer' in message or 'jenis-jenis' in message:
                return farming_knowledge[topic].get('jenis', farming_knowledge[topic].get('info', 'Maaf, informasi tentang jenis ' + topic + ' belum tersedia.'))
            elif 'perawatan' in message or 'merawat' in message or 'cara merawat' in message:
                return farming_knowledge[topic].get('perawatan', 'Maaf, informasi spesifik tentang perawatan ' + topic + ' belum tersedia.')
            elif 'pakan' in message or 'makan' in message or 'memberi makan' in message:
                return farming_knowledge[topic].get('pakan', 'Maaf, informasi tentang pakan ' + topic + ' belum tersedia.')
            elif 'reproduksi' in message or 'beranak' in message or 'kawin' in message or 'kebuntingan' in message:
                return farming_knowledge[topic].get('reproduksi', 'Maaf, informasi tentang reproduksi ' + topic + ' belum tersedia.')
            elif 'penyakit' in message or 'sakit' in message or 'virus' in message or 'bakteri' in message:
                return farming_knowledge[topic].get('penyakit', 'Maaf, informasi tentang penyakit ' + topic + ' belum tersedia.')
            elif 'produksi' in message or 'hasil' in message or 'produktivitas' in message:
                return farming_knowledge[topic].get('produksi', 'Maaf, informasi tentang produksi ' + topic + ' belum tersedia.')
            elif 'kolam' in message or 'kandang' in message or 'habitat' in message:
                return farming_knowledge[topic].get('kolam', farming_knowledge[topic].get('kandang', 'Maaf, informasi tentang kandang/kolam ' + topic + ' belum tersedia.'))
            else:
                # Return general info if no specific aspect mentioned
                return farming_knowledge[topic]['info']
    
    # Pertanyaan umum tentang peternakan
    for intent in ['modal_peternakan', 'mulai_beternak', 'cuaca']:
        for pattern in intents[intent]["patterns"]:
            if pattern in message:
                return random.choice(intents[intent]["responses"])
    
    # Jika tanggal atau waktu diminta
    if any(kw in message for kw in ["tanggal", "hari ini", "waktu", "jam"]):
        now = datetime.now()
        date_str = now.strftime("%A, %d %B %Y")
        time_str = now.strftime("%H:%M:%S")
        return f"Sekarang adalah {date_str}, pukul {time_str}."
    
    # Jika menanyakan tentang pembuat chatbot
    if any(kw in message for kw in ["siapa pembuatmu", "siapa yang membuatmu", "siapa creator", "siapa yang membuat", "dibuat oleh"]):
        return "Chatbot ini dibuat oleh Galuh Adi Insani."
    
    # Default response jika tidak ada kecocokan
    return random.choice(intents["fallback"]["responses"])

# Function to visualize growth prediction
def plot_growth_prediction(result):
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Set the style
    sns.set_style("whitegrid")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the data
    days = list(range(len(result['weights'])))
    ax.plot(days, result['weights'], marker='o', linestyle='-', color='#1f77b4')
    
    # Add labels and title
    ax.set_xlabel('Hari')
    ax.set_ylabel('Berat (kg)')
    ax.set_title(f'Prediksi Pertumbuhan Ternak: {result["initial_weight"]} kg → {result["final_weight"]:.2f} kg')
    
    # Add text annotations
    ax.text(0.05, 0.95, f'Berat awal: {result["initial_weight"]} kg', transform=ax.transAxes)
    ax.text(0.05, 0.90, f'Berat akhir: {result["final_weight"]:.2f} kg', transform=ax.transAxes)
    ax.text(0.05, 0.85, f'Pertambahan total: {result["weight_gain"]:.2f} kg', transform=ax.transAxes)
    ax.text(0.05, 0.80, f'Periode: {result["days"]} hari', transform=ax.transAxes)
    
    # Return the figure
    return fig

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Main UI elements
st.title("🐄 Chatternak - Farming Chat Bot")
st.markdown("Chatbot cerdas untuk informasi peternakan dan pertanian")

# Sidebar with options
with st.sidebar:
    st.header("Tentang Chatternak")
    st.info("Chatternak adalah chatbot interaktif yang dapat memberikan informasi tentang peternakan dan pertanian.")
    
    st.header("Fitur")
    st.markdown("""
    - Informasi tentang hewan ternak:
        - 🐄 Sapi
        - 🐐 Kambing
        - 🐓 Ayam
        - 🦆 Bebek
        - 🐟 Ikan
        - 🐇 Kelinci
    - 🌱 Informasi pupuk organik
    - 📊 Analisis data pertanian
    - 📈 Prediksi pertumbuhan
    - 💰 Analisis ekonomi
    """)
    
    # Tool selection
    st.header("Alat Analisis")
    tool_option = st.selectbox(
        "Pilih alat analisis:",
        ["Chat", "Kalkulator Pakan", "Prediksi Pertumbuhan", "Analisis BEP"]
    )

# Main content based on selected tool
if tool_option == "Chat":
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input field for new messages
    if prompt := st.chat_input("Tanyakan sesuatu tentang peternakan..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display bot response
        with st.chat_message("assistant"):
            response = get_bot_response(prompt)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

elif tool_option == "Kalkulator Pakan":
    st.header("Kalkulator Kebutuhan Pakan")
    
    col1, col2 = st.columns(2)
    
    with col1:
        animal_type = st.selectbox(
            "Jenis Ternak",
            ["sapi", "kambing", "ayam", "bebek", "ikan", "kelinci"]
        )
        count = st.number_input("Jumlah Ternak (ekor)", min_value=1, value=10)
    
    with col2:
        default_weight = {"sapi": 400, "kambing": 40, "ayam": 2, "bebek": 3, "ikan": 0.5, "kelinci": 4}
        weight = st.number_input(
            "Berat Rata-rata (kg)", 
            min_value=0.1, 
            value=float(default_weight.get(animal_type, 1.0)),
            step=0.1
        )
    
    if st.button("Hitung Kebutuhan Pakan"):
        result = calculate_feed_needs(animal_type, count, weight)
        st.success(result)
        
        # Create bar chart for visualization
        feed_data = {
            'Periode': ['Harian', 'Bulanan'],
            'Kebutuhan Pakan (kg)': [
                weight * feed_rates[animal_type] * count,
                weight * feed_rates[animal_type] * count * 30
            ]
        }
        
        st.bar_chart(feed_data, x='Periode')

elif tool_option == "Prediksi Pertumbuhan":
    st.header("Prediksi Pertumbuhan Ternak")
    
    col1, col2 = st.columns(2)
    
    with col1:
        animal_type = st.selectbox(
            "Jenis Ternak",
            ["sapi", "kambing", "ayam", "bebek", "ikan", "kelinci"]
        )
        initial_weight = st.number_input("Berat Awal (kg)", min_value=0.1, value=1.0, step=0.1)
    
    with col2:
        daily_gain = st.number_input("Pertambahan Berat Harian (kg/hari)", min_value=0.001, value=0.1, step=0.01)
        days = st.number_input("Periode (hari)", min_value=1, value=30)
    
    if st.button("Prediksi Pertumbuhan"):
        result = predict_growth(initial_weight, daily_gain, days)
        
        if 'error' in result:
            st.error(f"Terjadi kesalahan: {result['error']}")
        else:
            st.success(f"Prediksi pertumbuhan {animal_type}:")
            st.write(f"- Berat awal: {result['initial_weight']} kg")
            st.write(f"- Berat akhir setelah {result['days']} hari: {result['final_weight']:.2f} kg")
            st.write(f"- Total pertambahan berat: {result['weight_gain']:.2f} kg")
            
            # Plot the growth prediction
            fig = plot_growth_prediction(result)
            st.pyplot(fig)

elif tool_option == "Analisis BEP":
    st.header("Analisis Break Even Point (BEP)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fixed_cost = st.number_input("Biaya Tetap (Rp)", min_value=0, value=10000000)
        price_per_unit = st.number_input("Harga Jual per Unit (Rp)", min_value=0, value=50000)
    
    with col2:
        variable_cost_per_unit = st.number_input("Biaya Variabel per Unit (Rp)", min_value=0, value=30000)
    
    if st.button("Hitung BEP"):
        if price_per_unit == variable_cost_per_unit:
            st.error("Harga jual sama dengan biaya variabel, BEP tidak dapat dihitung.")
        else:
            bep_units = fixed_cost / (price_per_unit - variable_cost_per_unit)
            bep_revenue = bep_units * price_per_unit
            
            st.success("Analisis BEP (Break Even Point):")
            st.write(f"- Jumlah unit pada titik impas: {bep_units:.2f} unit")
            st.write(f"- Pendapatan pada titik impas: Rp {bep_revenue:,.2f}")
            st.write(f"- Artinya Anda perlu menjual minimal {bep_units:.2f} unit untuk tidak rugi.")
            
            # Create BEP visualization
            import matplotlib.pyplot as plt
            
            # Create data for plotting
            units = np.linspace(0, bep_units * 2, 100)
            fixed_costs = np.ones_like(units) * fixed_cost
            variable_costs = units * variable_cost_per_unit
            total_costs = fixed_costs + variable_costs
            revenue = units * price_per_unit
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(units, fixed_costs, label='Biaya Tetap', linestyle='--')
            ax.plot(units, total_costs, label='Total Biaya')
            ax.plot(units, revenue, label='Pendapatan')
            
            # Mark BEP point
            ax.axvline(x=bep_units, color='r', linestyle=':', alpha=0.5)
            ax.axhline(y=bep_revenue, color='r', linestyle=':', alpha=0.5)
            ax.plot([bep_units], [bep_revenue], 'ro', markersize=8)
            ax.annotate(f'BEP ({bep_units:.1f} unit, Rp {bep_revenue:,.0f})', 
                        xy=(bep_units, bep_revenue),
                        xytext=(bep_units + 5, bep_revenue + fixed_cost * 0.1),
                        arrowprops=dict(facecolor='black', shrink=0.05, width=1.5))
            
            # Add labels and legend
            ax.set_xlabel('Jumlah Unit')
            ax.set_ylabel('Rupiah (Rp)')
            ax.set_title('Analisis Break Even Point (BEP)')
            ax.grid(True)
            ax.legend()
            
            # Show the plot
            st.pyplot(fig)

# Footer
st.markdown("---")
st.markdown("© 2025 Chatternak - Farming Chat Bot | Created with Streamlit")