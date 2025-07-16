import requests
import os
from dotenv import load_dotenv
load_dotenv()


# Get API key from env
HF_API_KEY = os.getenv('HF_API_KEY')  # Make sure this is set!

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

# The text you want to analyze
input_text = "I’m so thrilled today!"

# API endpoint
url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"

# Send request
response = requests.post(url, headers=headers, json={"inputs": input_text})

# Check status
if response.status_code == 200:
    result = response.json()
    print("✅ Hugging Face API Result:")
    print(result)
else:
    print("❌ Failed to fetch from Hugging Face API")
    print("Status code:", response.status_code)
    print("Response:", response.text)
