#!/bin/bash

# Extract Gemini API key from .env file
if [ -f ".env" ]; then
  export GEMINI_API_KEY=$(grep "GEMINI_API_KEY" .env | cut -d'=' -f2)
  echo "Gemini API key loaded from .env file"
else
  echo "Warning: .env file not found. Make sure your API keys are properly set."
fi

# Aktivasi lingkungan virtual jika menggunakan venv/conda (hapus komentar jika digunakan)
# source venv/bin/activate
# conda activate chatternak_env

echo "Memulai Chatternak Streamlit App..."
streamlit run streamlit_app.py