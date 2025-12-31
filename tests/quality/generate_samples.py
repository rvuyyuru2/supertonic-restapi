import asyncio
import httpx
import os
import time
import statistics

API_URL = "http://localhost:8800"
API_KEY = "rLKAAK9R8d2qiqZo7ijUvfEon-BwvupDzeBzJjMko_Q" 

VOICES = ["alloy"]
# "echo", "fable", "onyx", "nova", "shimmer"
# Diverse Scenarios for holistic testing
SCENARIOS = {
    "Standard": "Supertonic provides high quality, low latency text to speech.",
    "Numbers": "Please dial 555-0199 for assistance. The code is 4, 8, 15, 16.",
    "Currency": "That will be $19.99, plus a €5.00 shipping fee. Total is £25.",
    "Dates": "The meeting is scheduled for January 5th, 2024 at 2:30 PM.",
    "Technical": "The API endpoint returns a JSON object via HTTPS headers FROM www.supertonic.ai.",
    "Conversational": "Wait... did you hear that? I think—nevermind, it's nothing.",
}

# Long text for stress testing streaming stability
LONG_TEXT = (
    "This is a longer text designed to test the streaming capabilities of the realtime text-to-speech engine. "
    "It contains multiple sentences to ensure that the system allows for continuous audio generation without "
    "significant buffers or pauses between segments. The goal is to verify that the Time To First Byte (TTFB) "
    "remains low regardless of the input length, and that the audio chunks arrive in a steady stream consistent "
    "with playback speed."
)

async def test_stream_sample(client, voice, text, index, label="Single"):
    """
    Generates audio and measures:
    - TTFB: Time to First Byte (latency)
    - Total Time: Full generation duration
    - Chunk Count: Number of streaming chunks received
    """
    url = f"{API_URL}/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": text,
        "voice": voice,
        "response_format": "mp3",
        "speed": 1.0
    }

    start_time = time.time()
    ttfb = None
    chunk_count = 0
    file_size = 0
    
    filename = f"tests/samples/{label}_{voice}_{index}.mp3"

    try:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                print(f"[{label}] Failed: {response.status_code} - {await response.aread()}")
                return None

            with open(filename, "wb") as f:
                async for chunk in response.aiter_bytes():
                    if ttfb is None:
                        ttfb = time.time() - start_time
                    f.write(chunk)
                    chunk_count += 1
                    file_size += len(chunk)

        total_time = time.time() - start_time
        
        # Fallback if no chunks received (shouldn't happen on 200 OK)
        if ttfb is None: ttfb = total_time 

        print(f"[{label}] {voice:<8} | TTFB: {ttfb*1000:6.1f}ms | Total: {total_time:5.2f}s | Chunks: {chunk_count:4} | Size: {file_size/1024:5.1f}KB")
        return {"ttfb": ttfb, "total": total_time}

    except Exception as e:
        print(f"[{label}] Error: {e}")
        return None

async def main():
    if not os.path.exists("tests/samples"):
        os.makedirs("tests/samples")

    print(f"--- Starting Realtime TTS Tests on {API_URL} ---\n")
    
    results = []

    async with httpx.AsyncClient() as client:
        # 1. Scenario-based Tests
        print("1. Diverse Scenario Tests (All Voices)")
        for voice in VOICES:
            print(f"--- Voice: {voice} ---")
            for category, text in SCENARIOS.items():
                stats = await test_stream_sample(client, voice, text, 0, label=category)
                if stats: results.append(stats)
        
        # 2. Long Text Streaming Test
        print("\n2. Long Text Streaming Stability")
        await test_stream_sample(client, "onyx", LONG_TEXT, 99, label="Long")

        # 3. Concurrent Load Test
        print("\n3. Concurrent Load Test (Simulating 5 users)")
        tasks = []
        for i in range(5):
            tasks.append(test_stream_sample(client, "nova", SCENARIOS["Standard"], i, label=f"Conc-{i}"))
        
        concurrent_results = await asyncio.gather(*tasks)
        for r in concurrent_results:
            if r: results.append(r)

    # 4. Summary Statistics
    if results:
        avg_ttfb = statistics.mean([r["ttfb"] for r in results]) * 1000
        avg_total = statistics.mean([r["total"] for r in results])
        print("\n--- Performance Summary ---")
        print(f"Average TTFB:       {avg_ttfb:.2f} ms")
        print(f"Average Generation: {avg_total:.2f} s")
        print("---------------------------")
    else:
        print("\nNo results gathered. Check connection/errors.")

if __name__ == "__main__":
    print("Ensure you have a valid API Key and the server is running.")
    asyncio.run(main())
