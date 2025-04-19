#!/bin/bash

# Source the API keys from .env file
if [ -f ".env" ]; then
  GEMINI_API_KEY=$(grep "GEMINI_API_KEY" .env | cut -d'=' -f2)
  echo "Gemini API key loaded"
else
  echo "Error: .env file not found. Please create a .env file with your GEMINI_API_KEY."
  exit 1
fi

# Make API request to Gemini
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
-H 'Content-Type: application/json' \
-X POST \
-d '{
  "contents": [{
    "parts":[{"text": "'"$1"'"}]
    }]
}'

echo -e "\n"