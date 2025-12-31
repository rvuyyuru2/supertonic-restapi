import httpx
import os
import json

API_URL = "http://localhost:8800"
API_KEY = "rLKAAK9R8d2qiqZo7ijUvfEon-BwvupDzeBzJjMko_Q" # Need to create one first

VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
TEXTS = [
    "The quick brown fox jumps over the lazy dog.",
    "Supertonic provides high quality, low latency text to speech for production applications.",
    "1, 2, 3, 4, 5. Testing numbers and punctuation! Does it sound natural?",
]

def generate_samples():
    if not os.path.exists("tests/samples"):
        os.makedirs("tests/samples")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    for voice in VOICES:
        for i, text in enumerate(TEXTS):
            print(f"Generating sample for voice: {voice}, text index: {i}")
            payload = {
                "input": text,
                "voice": voice,
                "response_format": "mp3",
                "speed": 1.0
            }
            
            response = httpx.post(f"{API_URL}/v1/audio/speech", json=payload, headers=headers)
            
            if response.status_code == 200:
                filename = f"tests/samples/{voice}_sample_{i}.mp3"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"Saved {filename}")
            else:
                print(f"Failed for {voice}: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Note: You must create an API key first using /auth/create-key
    print("Ensure you have a valid API Key and the server is running.")
    # API_KEY = input("Enter your Bearer Token: ")
    generate_samples()
