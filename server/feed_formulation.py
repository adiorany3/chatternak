from __future__ import annotations

from typing import Dict, List, Tuple

# Katalog bahan pakan umum di Indonesia.
# Angka protein dan energi adalah estimasi edukatif berbasis bahan as-fed/umum lapangan,
# bukan pengganti hasil uji laboratorium. Gunakan sebagai baseline formulasi awal.
LOCAL_FEED_INGREDIENTS: Dict[str, Dict[str, float | str]] = {
    # Hijauan rumput dan sumber serat ruminansia
    "rumput odot": {"protein": 10.0, "energy": 55.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia,kelinci", "note": "Hijauan populer untuk sapi, kambing, domba; berikan segar/layu."},
    "rumput gajah": {"protein": 8.0, "energy": 52.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia,kelinci", "note": "Sumber serat utama; cacah untuk mengurangi seleksi pakan."},
    "rumput pakchong": {"protein": 10.0, "energy": 56.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia", "note": "Varietas rumput potong produktif; cocok untuk silase."},
    "rumput raja": {"protein": 8.5, "energy": 53.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia", "note": "Hijauan potong untuk ruminansia."},
    "rumput setaria": {"protein": 9.0, "energy": 52.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia,kelinci", "note": "Sumber serat; baik dicacah."},
    "rumput benggala": {"protein": 9.5, "energy": 54.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia", "note": "Hijauan padang gembala/potong."},
    "rumput lapangan": {"protein": 7.0, "energy": 48.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia,kelinci", "note": "Kualitas sangat bervariasi; hindari tercemar pestisida."},
    "tebon jagung": {"protein": 8.0, "energy": 60.0, "type": "hijauan energi", "category": "Hijauan", "species": "ruminansia", "note": "Baik untuk silase; energi relatif lebih tinggi."},
    "jerami padi": {"protein": 4.0, "energy": 40.0, "type": "serat kasar", "category": "Hijauan", "species": "ruminansia", "note": "Serat rendah protein; lebih baik diamoniasi/fermentasi."},
    "jerami jagung": {"protein": 5.5, "energy": 44.0, "type": "serat kasar", "category": "Hijauan", "species": "ruminansia", "note": "Manfaatkan sebagai sumber serat; perlu suplementasi protein."},
    "jerami kacang tanah": {"protein": 10.0, "energy": 48.0, "type": "serat leguminosa", "category": "Hijauan", "species": "ruminansia", "note": "Lebih baik dari jerami padi; cek jamur/aflatoksin."},
    "pucuk tebu": {"protein": 5.0, "energy": 45.0, "type": "serat kasar", "category": "Hijauan", "species": "ruminansia", "note": "Sumber serat; perlu konsentrat/protein tambahan."},
    "klobot/tongkol jagung cincang": {"protein": 3.5, "energy": 45.0, "type": "serat energi", "category": "Hijauan", "species": "ruminansia", "note": "Bisa sebagai serat; kualitas rendah jika terlalu tua."},
    "limbah sayuran pasar": {"protein": 10.0, "energy": 45.0, "type": "hijauan basah", "category": "Hijauan", "species": "ruminansia,kelinci,babi", "note": "Sortir plastik/busuk; adaptasikan bertahap."},
    "daun pisang": {"protein": 8.0, "energy": 42.0, "type": "hijauan", "category": "Hijauan", "species": "ruminansia,kelinci", "note": "Tambahan serat; jangan menjadi satu-satunya pakan."},

    # Leguminosa dan daun protein
    "indigofera": {"protein": 24.0, "energy": 58.0, "type": "leguminosa protein", "category": "Leguminosa/Daun Protein", "species": "ruminansia,kelinci", "note": "Sumber protein hijauan; pemberian bertahap."},
    "kaliandra": {"protein": 20.0, "energy": 55.0, "type": "leguminosa tanin", "category": "Leguminosa/Daun Protein", "species": "ruminansia", "note": "Mengandung tanin; gunakan sebagai campuran, jangan berlebihan."},
    "lamtoro": {"protein": 22.0, "energy": 56.0, "type": "leguminosa protein", "category": "Leguminosa/Daun Protein", "species": "ruminansia", "note": "Ada mimosin; adaptasi dan batasi pemberian."},
    "gamal": {"protein": 20.0, "energy": 55.0, "type": "leguminosa", "category": "Leguminosa/Daun Protein", "species": "ruminansia", "note": "Layu-kan dulu untuk meningkatkan palatabilitas."},
    "turi": {"protein": 24.0, "energy": 55.0, "type": "leguminosa", "category": "Leguminosa/Daun Protein", "species": "ruminansia,kelinci", "note": "Sumber protein daun; campurkan bertahap."},
    "daun singkong": {"protein": 22.0, "energy": 55.0, "type": "daun protein", "category": "Leguminosa/Daun Protein", "species": "ruminansia,kelinci", "note": "Layu/fermentasi untuk menurunkan risiko HCN; jangan segar berlebihan."},
    "daun pepaya": {"protein": 18.0, "energy": 50.0, "type": "daun tambahan", "category": "Leguminosa/Daun Protein", "species": "ruminansia,unggas", "note": "Tambahan terbatas; rasa pahit bisa menurunkan konsumsi."},
    "azolla": {"protein": 20.0, "energy": 45.0, "type": "hijauan air protein", "category": "Leguminosa/Daun Protein", "species": "unggas,ikan,ruminansia", "note": "Gunakan bersih; adaptasi bertahap."},
    "eceng gondok fermentasi": {"protein": 10.0, "energy": 38.0, "type": "hijauan air", "category": "Leguminosa/Daun Protein", "species": "ruminansia,babi,ikan", "note": "Harus bersih dan diolah; cek cemaran logam berat."},

    # Silase, fermentasi, dan pakan awetan
    "silase jagung": {"protein": 8.0, "energy": 64.0, "type": "silase energi", "category": "Silase/Fermentasi", "species": "ruminansia", "note": "Pakan awetan energi; pastikan tidak berjamur."},
    "silase rumput": {"protein": 8.5, "energy": 55.0, "type": "silase hijauan", "category": "Silase/Fermentasi", "species": "ruminansia", "note": "Baik untuk cadangan musim kemarau."},
    "hay/rumput kering": {"protein": 7.5, "energy": 50.0, "type": "hijauan kering", "category": "Silase/Fermentasi", "species": "ruminansia,kelinci", "note": "Sumber serat kering; simpan di tempat kering."},
    "complete feed fermentasi": {"protein": 12.0, "energy": 62.0, "type": "pakan lengkap", "category": "Silase/Fermentasi", "species": "ruminansia", "note": "Komposisi tergantung bahan; cek bau asam segar, bukan busuk."},
    "jerami amoniasi": {"protein": 6.5, "energy": 45.0, "type": "serat olahan", "category": "Silase/Fermentasi", "species": "ruminansia", "note": "Opsi peningkatan jerami; proses harus benar dan aman."},
    "dedak fermentasi": {"protein": 12.0, "energy": 66.0, "type": "energi fermentasi", "category": "Silase/Fermentasi", "species": "ruminansia,unggas,babi,ikan", "note": "Kualitas tergantung proses; hindari jamur."},
    "ampas tahu fermentasi": {"protein": 18.0, "energy": 62.0, "type": "protein basah", "category": "Silase/Fermentasi", "species": "ruminansia,babi,ikan", "note": "Cepat basi jika basah; simpan/fermentasi dengan benar."},

    # Sumber energi dan karbohidrat
    "jagung giling": {"protein": 8.5, "energy": 85.0, "type": "energi", "category": "Energi/Karbohidrat", "species": "unggas,ruminansia,babi,ikan,kelinci", "note": "Energi utama; cek kadar air dan jamur."},
    "dedak padi": {"protein": 12.0, "energy": 68.0, "type": "energi-serat", "category": "Energi/Karbohidrat", "species": "ruminansia,unggas,babi,ikan,kelinci", "note": "Umum di Indonesia; kualitas sangat bervariasi."},
    "bekatul": {"protein": 11.0, "energy": 66.0, "type": "energi-serat", "category": "Energi/Karbohidrat", "species": "ruminansia,unggas,babi,ikan,kelinci", "note": "Mirip dedak; cek ketengikan."},
    "pollard": {"protein": 15.0, "energy": 70.0, "type": "energi-protein", "category": "Energi/Karbohidrat", "species": "ruminansia,unggas,babi,kelinci", "note": "Limbah gandum; palatabel untuk konsentrat."},
    "onggok": {"protein": 3.0, "energy": 72.0, "type": "energi singkong", "category": "Energi/Karbohidrat", "species": "ruminansia,babi,ikan", "note": "Energi murah; rendah protein, perlu sumber protein."},
    "gaplek/tepung singkong": {"protein": 2.5, "energy": 78.0, "type": "energi singkong", "category": "Energi/Karbohidrat", "species": "ruminansia,unggas,babi,ikan", "note": "Sumber energi; perlu balancing protein dan mineral."},
    "tepung tapioka": {"protein": 1.0, "energy": 80.0, "type": "energi pati", "category": "Energi/Karbohidrat", "species": "unggas,babi,ikan,ruminansia", "note": "Energi/binder; rendah protein."},
    "menir beras": {"protein": 7.5, "energy": 80.0, "type": "energi", "category": "Energi/Karbohidrat", "species": "unggas,babi,ikan", "note": "Sumber energi, tergantung harga lokal."},
    "nasi aking": {"protein": 7.0, "energy": 78.0, "type": "energi", "category": "Energi/Karbohidrat", "species": "unggas,babi,ikan", "note": "Harus kering dan bersih; hindari jamur/kapang."},
    "tepung roti/limbah bakery": {"protein": 10.0, "energy": 82.0, "type": "energi", "category": "Energi/Karbohidrat", "species": "ruminansia,unggas,babi,ikan", "note": "Cek garam, jamur, dan ketengikan."},
    "molases/tetes tebu": {"protein": 3.0, "energy": 75.0, "type": "energi cair", "category": "Energi/Karbohidrat", "species": "ruminansia", "note": "Palatabilitas dan energi; jangan berlebihan agar tidak mencret."},
    "minyak sawit/cpo": {"protein": 0.0, "energy": 100.0, "type": "lemak energi", "category": "Energi/Karbohidrat", "species": "unggas,babi,ruminansia,ikan", "note": "Energi tinggi; dosis kecil dan campur merata."},
    "minyak kelapa": {"protein": 0.0, "energy": 100.0, "type": "lemak energi", "category": "Energi/Karbohidrat", "species": "unggas,babi,ruminansia", "note": "Energi tinggi; gunakan terbatas."},

    # Protein nabati dan agroindustri
    "bungkil kedelai": {"protein": 44.0, "energy": 78.0, "type": "protein nabati", "category": "Protein Nabati", "species": "unggas,babi,ikan,ruminansia,kelinci", "note": "Protein berkualitas; harga relatif tinggi."},
    "bungkil kelapa": {"protein": 20.0, "energy": 65.0, "type": "protein-serat", "category": "Protein Nabati", "species": "ruminansia,unggas,babi,ikan", "note": "Umum di Indonesia; cek jamur/ketengikan."},
    "bungkil inti sawit": {"protein": 16.0, "energy": 60.0, "type": "protein-serat", "category": "Protein Nabati", "species": "ruminansia", "note": "Baik untuk ruminansia; terbatas untuk unggas karena serat."},
    "bungkil kacang tanah": {"protein": 42.0, "energy": 72.0, "type": "protein nabati", "category": "Protein Nabati", "species": "unggas,babi,ruminansia,ikan", "note": "Wajib cek risiko aflatoksin."},
    "ampas tahu basah": {"protein": 18.0, "energy": 62.0, "type": "protein basah", "category": "Protein Nabati", "species": "ruminansia,babi,ikan", "note": "Cepat basi; berikan segar atau fermentasi."},
    "ampas tahu kering": {"protein": 22.0, "energy": 64.0, "type": "protein", "category": "Protein Nabati", "species": "ruminansia,babi,ikan,unggas", "note": "Lebih stabil daripada basah; cek kadar air."},
    "ampas tempe": {"protein": 20.0, "energy": 60.0, "type": "protein", "category": "Protein Nabati", "species": "ruminansia,babi,ikan", "note": "Gunakan segar/diolah; kualitas bervariasi."},
    "ampas kecap": {"protein": 20.0, "energy": 55.0, "type": "protein asin", "category": "Protein Nabati", "species": "ruminansia,babi", "note": "Perhatikan kadar garam; batasi penggunaan."},
    "ampas bir/brewer grain": {"protein": 22.0, "energy": 60.0, "type": "protein basah", "category": "Protein Nabati", "species": "ruminansia,babi", "note": "Baik untuk sapi perah/potong; cepat rusak jika basah."},
    "ddgs jagung": {"protein": 27.0, "energy": 72.0, "type": "protein-energi", "category": "Protein Nabati", "species": "unggas,babi,ruminansia,ikan", "note": "Bahan pakan impor/lokal tertentu; cek kualitas."},
    "corn gluten meal": {"protein": 55.0, "energy": 78.0, "type": "protein tinggi", "category": "Protein Nabati", "species": "unggas,ikan,babi", "note": "Protein tinggi; gunakan sesuai formula."},
    "tepung daun kelor": {"protein": 25.0, "energy": 55.0, "type": "protein daun", "category": "Protein Nabati", "species": "unggas,ruminansia,kelinci", "note": "Tambahan protein/pigmen; batasi agar palatabilitas terjaga."},

    # Protein hewani dan sumber asam amino
    "tepung ikan": {"protein": 55.0, "energy": 75.0, "type": "protein hewani", "category": "Protein Hewani", "species": "unggas,ikan,babi", "note": "Protein berkualitas; cek bau tengik dan kadar garam."},
    "tepung kepala udang": {"protein": 35.0, "energy": 55.0, "type": "protein hewani", "category": "Protein Hewani", "species": "unggas,ikan", "note": "Sumber protein/mineral; serat kitin cukup tinggi."},
    "tepung darah": {"protein": 80.0, "energy": 65.0, "type": "protein hewani tinggi", "category": "Protein Hewani", "species": "unggas,babi,ikan", "note": "Protein tinggi; palatabilitas dan proses harus baik."},
    "tepung daging tulang/mbm": {"protein": 45.0, "energy": 70.0, "type": "protein-mineral", "category": "Protein Hewani", "species": "unggas,babi,ikan", "note": "Cek regulasi, kualitas, dan keamanan bahan."},
    "tepung bulu terhidrolisis": {"protein": 75.0, "energy": 55.0, "type": "protein hewani", "category": "Protein Hewani", "species": "unggas,babi,ikan", "note": "Hanya jika proses hidrolisis baik; kecernaan bervariasi."},
    "maggot bsf segar": {"protein": 35.0, "energy": 70.0, "type": "protein serangga", "category": "Protein Hewani", "species": "unggas,ikan,babi", "note": "Sumber protein/lemak; gunakan bahan bersih."},
    "tepung maggot bsf": {"protein": 42.0, "energy": 75.0, "type": "protein serangga", "category": "Protein Hewani", "species": "unggas,ikan,babi", "note": "Lebih stabil dari segar; cek kadar lemak dan proses."},
    "cacing sutra": {"protein": 55.0, "energy": 65.0, "type": "pakan alami", "category": "Protein Hewani", "species": "ikan", "note": "Untuk benih ikan; harus bersih dari cemaran."},
    "keong mas olahan": {"protein": 45.0, "energy": 60.0, "type": "protein hewani", "category": "Protein Hewani", "species": "unggas,ikan", "note": "Rebus/olah; jangan berikan mentah berisiko parasit."},
    "limbah ikan olahan": {"protein": 45.0, "energy": 65.0, "type": "protein hewani", "category": "Protein Hewani", "species": "unggas,ikan,babi", "note": "Harus segar/diolah; hindari busuk dan garam tinggi."},

    # Pakan komersial/konsentrat
    "konsentrat sapi potong": {"protein": 14.0, "energy": 70.0, "type": "konsentrat", "category": "Konsentrat/Pakan Komersial", "species": "ruminansia", "note": "Gunakan sesuai label dan target ADG."},
    "konsentrat sapi perah": {"protein": 16.0, "energy": 72.0, "type": "konsentrat", "category": "Konsentrat/Pakan Komersial", "species": "ruminansia", "note": "Diformulasikan untuk produksi susu."},
    "konsentrat kambing/domba": {"protein": 16.0, "energy": 70.0, "type": "konsentrat", "category": "Konsentrat/Pakan Komersial", "species": "ruminansia", "note": "Untuk penggemukan/laktasi; adaptasi bertahap."},
    "pakan broiler starter": {"protein": 21.0, "energy": 82.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "unggas", "note": "Untuk fase awal broiler; ikuti label pabrik."},
    "pakan broiler finisher": {"protein": 19.0, "energy": 84.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "unggas", "note": "Untuk fase akhir broiler."},
    "pakan layer": {"protein": 17.0, "energy": 78.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "unggas", "note": "Untuk ayam petelur; pastikan cukup kalsium."},
    "konsentrat ayam kampung/joper": {"protein": 18.0, "energy": 78.0, "type": "konsentrat unggas", "category": "Konsentrat/Pakan Komersial", "species": "unggas", "note": "Campuran praktis untuk ayam kampung/joper."},
    "pakan bebek/itik petelur": {"protein": 17.0, "energy": 76.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "unggas", "note": "Untuk itik petelur; cek kualitas bahan basah jika dicampur."},
    "pakan puyuh petelur": {"protein": 20.0, "energy": 78.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "unggas", "note": "Untuk puyuh produksi telur."},
    "pelet kelinci": {"protein": 16.0, "energy": 65.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "kelinci", "note": "Utamakan serat cukup; air bersih selalu tersedia."},
    "pelet ikan apung": {"protein": 30.0, "energy": 75.0, "type": "pelet ikan", "category": "Konsentrat/Pakan Komersial", "species": "ikan", "note": "Memudahkan kontrol konsumsi; pilih ukuran sesuai ikan."},
    "pelet ikan tenggelam": {"protein": 28.0, "energy": 72.0, "type": "pelet ikan", "category": "Konsentrat/Pakan Komersial", "species": "ikan", "note": "Cocok untuk beberapa sistem; kontrol sisa pakan."},
    "pakan babi starter": {"protein": 20.0, "energy": 82.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "babi", "note": "Untuk fase starter; ikuti label."},
    "pakan babi grower-finisher": {"protein": 16.0, "energy": 84.0, "type": "pakan komplit", "category": "Konsentrat/Pakan Komersial", "species": "babi", "note": "Untuk pembesaran/penggemukan."},

    # Mineral, vitamin, dan aditif legal umum
    "mineral mix": {"protein": 0.0, "energy": 0.0, "type": "mineral", "category": "Mineral/Vitamin/Aditif", "species": "umum", "note": "Sumber mineral mikro/makro; ikuti dosis label."},
    "premix vitamin-mineral": {"protein": 0.0, "energy": 0.0, "type": "premix", "category": "Mineral/Vitamin/Aditif", "species": "umum", "note": "Ikuti dosis label; jangan over dosis."},
    "garam": {"protein": 0.0, "energy": 0.0, "type": "mineral natrium", "category": "Mineral/Vitamin/Aditif", "species": "ruminansia,unggas,babi", "note": "Gunakan terbatas; cek total garam formula."},
    "kapur/kalsium karbonat": {"protein": 0.0, "energy": 0.0, "type": "mineral kalsium", "category": "Mineral/Vitamin/Aditif", "species": "unggas,ruminansia,babi", "note": "Penting untuk layer; seimbangkan dengan fosfor."},
    "tepung tulang": {"protein": 0.0, "energy": 0.0, "type": "mineral ca-p", "category": "Mineral/Vitamin/Aditif", "species": "unggas,babi,ruminansia", "note": "Sumber kalsium/fosfor; cek keamanan bahan."},
    "dcp/dicalcium phosphate": {"protein": 0.0, "energy": 0.0, "type": "mineral fosfor", "category": "Mineral/Vitamin/Aditif", "species": "umum", "note": "Sumber Ca/P; ikuti formula."},
    "mcp/monocalcium phosphate": {"protein": 0.0, "energy": 0.0, "type": "mineral fosfor", "category": "Mineral/Vitamin/Aditif", "species": "umum", "note": "Sumber fosfor; ikuti formula."},
    "grit/kerang giling": {"protein": 0.0, "energy": 0.0, "type": "kalsium/grit", "category": "Mineral/Vitamin/Aditif", "species": "unggas", "note": "Untuk layer/unggas; bantu kalsium dan pencernaan mekanis."},
    "lisin": {"protein": 0.0, "energy": 0.0, "type": "asam amino", "category": "Mineral/Vitamin/Aditif", "species": "unggas,babi,ikan", "note": "Aditif formulasi; gunakan sesuai dosis ahli/label."},
    "metionin": {"protein": 0.0, "energy": 0.0, "type": "asam amino", "category": "Mineral/Vitamin/Aditif", "species": "unggas,babi,ikan", "note": "Aditif formulasi; gunakan sesuai dosis ahli/label."},
    "probiotik pakan": {"protein": 0.0, "energy": 0.0, "type": "aditif", "category": "Mineral/Vitamin/Aditif", "species": "umum", "note": "Ikuti label; bukan pengganti manajemen pakan bersih."},
    "ragi/yeast": {"protein": 40.0, "energy": 55.0, "type": "aditif protein", "category": "Mineral/Vitamin/Aditif", "species": "ruminansia,unggas,babi,ikan", "note": "Aditif/palatabilitas; gunakan terbatas."},
    "toxin binder": {"protein": 0.0, "energy": 0.0, "type": "aditif pengikat mikotoksin", "category": "Mineral/Vitamin/Aditif", "species": "umum", "note": "Membantu risiko mikotoksin; tetap wajib perbaiki kualitas bahan."},
}

FEED_CATEGORY_ORDER = [
    "Semua kategori",
    "Hijauan",
    "Leguminosa/Daun Protein",
    "Silase/Fermentasi",
    "Energi/Karbohidrat",
    "Protein Nabati",
    "Protein Hewani",
    "Konsentrat/Pakan Komersial",
    "Mineral/Vitamin/Aditif",
]

ANIMAL_GROUPS = {
    "sapi": "ruminansia",
    "kerbau": "ruminansia",
    "kambing": "ruminansia",
    "domba": "ruminansia",
    "ayam": "unggas",
    "bebek": "unggas",
    "itik": "unggas",
    "puyuh": "unggas",
    "ikan lele": "ikan",
    "ikan nila": "ikan",
    "ikan gurame": "ikan",
    "ikan patin": "ikan",
    "ikan mas": "ikan",
    "kelinci": "kelinci",
    "babi": "babi",
}

TARGET_PROTEIN: Dict[Tuple[str, str], float] = {
    ("sapi", "penggemukan"): 12.0,
    ("sapi", "laktasi"): 14.0,
    ("kerbau", "penggemukan"): 11.0,
    ("kerbau", "laktasi"): 13.0,
    ("kambing", "penggemukan"): 13.0,
    ("kambing", "bunting tua"): 14.0,
    ("kambing", "laktasi"): 15.0,
    ("domba", "penggemukan"): 13.0,
    ("domba", "bunting tua"): 14.0,
    ("ayam", "starter"): 20.0,
    ("ayam", "grower"): 17.0,
    ("ayam", "finisher"): 18.0,
    ("ayam", "layer awal produksi"): 17.0,
    ("bebek", "petelur"): 17.0,
    ("puyuh", "petelur"): 20.0,
    ("babi", "starter"): 20.0,
    ("babi", "grower"): 17.0,
    ("babi", "finisher"): 15.0,
    ("ikan lele", "pembesaran"): 30.0,
    ("ikan nila", "pembesaran"): 28.0,
    ("ikan gurame", "pembesaran"): 26.0,
    ("ikan patin", "pembesaran"): 28.0,
    ("ikan mas", "pembesaran"): 28.0,
    ("kelinci", "penggemukan"): 16.0,
}


def _animal_group(animal_type: str) -> str:
    animal = (animal_type or "").lower().strip()
    return ANIMAL_GROUPS.get(animal, animal)


def feed_categories() -> List[str]:
    existing = sorted({str(v.get("category", v.get("type", "Lainnya"))) for v in LOCAL_FEED_INGREDIENTS.values()})
    ordered = [c for c in FEED_CATEGORY_ORDER if c == "Semua kategori" or c in existing]
    for c in existing:
        if c not in ordered:
            ordered.append(c)
    return ordered


def is_ingredient_suitable(name: str, animal_type: str) -> bool:
    info = LOCAL_FEED_INGREDIENTS.get(name, {})
    species = str(info.get("species", "umum")).lower()
    group = _animal_group(animal_type)
    animal = (animal_type or "").lower().strip()
    return "umum" in species or group in species or animal in species


def feed_options_for_animal(animal_type: str, category: str = "Semua kategori", include_all_if_empty: bool = True) -> List[str]:
    category = category or "Semua kategori"
    options: List[str] = []
    for name, info in LOCAL_FEED_INGREDIENTS.items():
        if category != "Semua kategori" and str(info.get("category", "")) != category:
            continue
        if is_ingredient_suitable(name, animal_type):
            options.append(name)
    if not options and include_all_if_empty:
        for name, info in LOCAL_FEED_INGREDIENTS.items():
            if category == "Semua kategori" or str(info.get("category", "")) == category:
                options.append(name)
    return sorted(options, key=lambda n: (str(LOCAL_FEED_INGREDIENTS[n].get("category", "")), n))


def feed_option_label(name: str) -> str:
    info = LOCAL_FEED_INGREDIENTS.get(name, {})
    pk = info.get("protein", 0)
    category = info.get("category", info.get("type", ""))
    return f"{name} — {category} | PK ±{pk}%"


def feed_catalog_rows(animal_type: str = "", category: str = "Semua kategori", only_suitable: bool = False) -> List[Dict[str, str | float]]:
    names = feed_options_for_animal(animal_type, category) if only_suitable else [
        name for name, info in LOCAL_FEED_INGREDIENTS.items()
        if category == "Semua kategori" or str(info.get("category", "")) == category
    ]
    rows = []
    for name in sorted(names, key=lambda n: (str(LOCAL_FEED_INGREDIENTS[n].get("category", "")), n)):
        info = LOCAL_FEED_INGREDIENTS[name]
        rows.append({
            "Bahan": name,
            "Kategori": str(info.get("category", "")),
            "Jenis": str(info.get("type", "")),
            "Protein estimasi (%)": float(info.get("protein", 0) or 0),
            "Indeks energi": float(info.get("energy", 0) or 0),
            "Cocok untuk": str(info.get("species", "umum")),
            "Catatan lapangan": str(info.get("note", "")),
        })
    return rows


def ingredient_notes(names: List[str]) -> List[str]:
    notes = []
    for name in names:
        note = str(LOCAL_FEED_INGREDIENTS.get(name, {}).get("note", "")).strip()
        if note:
            notes.append(f"- {name}: {note}")
    return notes


def target_protein(animal_type: str, phase: str) -> float:
    animal = (animal_type or "").lower()
    ph = (phase or "").lower()
    for (a, p), target in TARGET_PROTEIN.items():
        if a == animal and p in ph:
            return target
    defaults = {"sapi": 12.0, "kerbau": 11.0, "kambing": 13.0, "domba": 13.0, "ayam": 18.0, "bebek": 17.0, "puyuh": 20.0, "kelinci": 16.0, "babi": 17.0, "ikan lele": 30.0, "ikan nila": 28.0, "ikan gurame": 26.0, "ikan patin": 28.0, "ikan mas": 28.0}
    return defaults.get(animal, 14.0)


def calculate_formula(ingredients: List[Dict[str, float | str]]) -> Dict[str, float]:
    total_pct = sum(float(item.get("percent", 0) or 0) for item in ingredients)
    if total_pct <= 0:
        return {"total_percent": 0.0, "protein": 0.0, "energy_index": 0.0}
    protein = 0.0
    energy = 0.0
    for item in ingredients:
        pct = float(item.get("percent", 0) or 0)
        protein += pct * float(item.get("protein", 0) or 0)
        energy += pct * float(item.get("energy", 0) or 0)
    return {
        "total_percent": total_pct,
        "protein": protein / total_pct,
        "energy_index": energy / total_pct,
    }


def estimate_formula_cost(ingredients: List[Dict[str, float | str]]) -> float:
    total_pct = sum(float(item.get("percent", 0) or 0) for item in ingredients)
    if total_pct <= 0:
        return 0.0
    cost = 0.0
    for item in ingredients:
        cost += float(item.get("percent", 0) or 0) * float(item.get("price_per_kg", 0) or 0)
    return cost / total_pct


def formula_feedback(animal_type: str, phase: str, ingredients: List[Dict[str, float | str]]) -> str:
    result = calculate_formula(ingredients)
    cost = estimate_formula_cost(ingredients)
    target = target_protein(animal_type, phase)
    diff = result["protein"] - target
    if result["total_percent"] <= 0:
        return "Formula belum berisi bahan. Tambahkan bahan pakan dan persentasenya."
    total_note = "tepat 100%" if abs(result["total_percent"] - 100) < 0.01 else f"belum 100% ({result['total_percent']:.1f}%)"
    if diff >= 1.5:
        protein_note = "protein cenderung tinggi; cek biaya, keseimbangan energi, dan risiko pemborosan."
    elif diff <= -1.5:
        protein_note = "protein cenderung rendah; pertimbangkan sumber protein seperti bungkil kedelai, bungkil kelapa, ampas tahu, indigofera, tepung ikan, atau maggot sesuai komoditas."
    else:
        protein_note = "protein mendekati target awal."

    selected_names = [str(item.get("name", "")) for item in ingredients if item.get("name")]
    not_suitable = [name for name in selected_names if not is_ingredient_suitable(name, animal_type)]
    compatibility_note = ""
    if not_suitable:
        compatibility_note = "\n- Perhatian kesesuaian komoditas: cek kembali penggunaan " + ", ".join(not_suitable) + "."

    notes = ingredient_notes(selected_names[:8])
    note_block = ""
    if notes:
        note_block = "\n\nCatatan bahan terpilih:\n" + "\n".join(notes)

    return (
        "Evaluasi formula pakan:\n"
        f"- Total komposisi: {total_note}\n"
        f"- Protein kasar estimasi: {result['protein']:.2f}% | target fase: ±{target:.1f}%\n"
        f"- Indeks energi relatif: {result['energy_index']:.1f}/100\n"
        f"- Estimasi biaya campuran: Rp {cost:,.0f}/kg\n".replace(",", ".")
        + f"- Catatan: {protein_note}{compatibility_note}\n"
        + note_block
        + "\n\nCatatan lapangan: nilai ini estimasi edukatif. Untuk formula komersial, idealnya uji bahan, cek bahan kering, serat, mineral, mikotoksin, batas penggunaan bahan, dan performa aktual."
    )


def simple_ruminant_ration(animal_type: str, body_weight: float, population: int, forage_ratio: float = 70.0) -> str:
    bw = float(body_weight)
    pop = int(population)
    rates = {"sapi": 0.03, "kerbau": 0.025, "kambing": 0.04, "domba": 0.04}
    total_feed = bw * rates.get(animal_type, 0.035) * pop
    forage = total_feed * forage_ratio / 100
    concentrate = total_feed - forage
    return (
        f"Ransum awal {animal_type} {pop} ekor bobot rata-rata {bw:.1f} kg:\n"
        f"- Total pakan segar estimasi: {total_feed:.2f} kg/hari\n"
        f"- Hijauan ±{forage_ratio:.0f}%: {forage:.2f} kg/hari\n"
        f"- Konsentrat ±{100-forage_ratio:.0f}%: {concentrate:.2f} kg/hari\n"
        "- Adaptasikan bertahap 7-10 hari, jangan ganti pakan mendadak."
    )
