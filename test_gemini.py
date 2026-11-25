import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash-lite"

try:
    response = client.models.generate_content(
        model=MODEL, contents="Reply with the word SUCCESS."
    )

    print("Model test successful!")
    print("Response:", response.text)

except Exception as e:
    print("Model test failed!")
    print("Error:", e)
