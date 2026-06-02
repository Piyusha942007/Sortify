import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API Key found.")
    exit()

client = genai.Client(api_key=api_key)

print("--- AVAILABLE MODELS ---")
try:
    for model in client.models.list():
        print(f"Model Name: {model.name} | Supported Actions: {model.supported_actions}")
except Exception as e:
    print(f"Error listing models: {e}")
