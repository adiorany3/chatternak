@echo off
echo Memulai server Farming Chat Bot dengan Python...
echo Pastikan Anda telah menginstal dependensi yang diperlukan
echo Jika belum, jalankan: pip install -r requirements.txt
echo.

echo Setting up NLTK data packages...
python setup_nltk.py

python app.py
pause