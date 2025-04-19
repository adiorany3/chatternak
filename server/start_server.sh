#!/bin/bash

echo "Memulai server Farming Chat Bot dengan Python..."
echo "Pastikan Anda telah menginstal dependensi yang diperlukan"
echo "Jika belum, jalankan: pip install -r requirements.txt"
echo ""

cd "$(dirname "$0")"

# Determine Python command (python or python3)
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "Error: Neither python nor python3 was found. Please install Python."
        exit 1
    fi
fi

# Run NLTK setup script to download required data packages
echo "Setting up NLTK data packages..."
$PYTHON_CMD setup_nltk.py

# Start the application server
$PYTHON_CMD app.py