import asyncio
import httpx
import time
import statistics

API_URL = "http://localhost:8800/v1/audio/speech"
API_KEY = "rLKAAK9R8d2qiqZo7ijUvfEon-BwvupDzeBzJjMko_Q"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 50

payload = {
    "input": "This is a stress test for Supertonic TTS API. It should handle multiple concurrent requests smoothly.",
    "voice": "alloy",
    "response_format": "mp3",
    "speed": 1.0,
    "stream": False
}

async def make_request(client, i):
    start_time = time.perf_counter()
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = await client.post(API_URL, json=payload, headers=headers, timeout=60.0)
        end_time = time.perf_counter()
        latency = end_time - start_time
        if response.status_code == 200:
            return latency, True
        else:
            print(f"Request {i} failed: {response.status_code}")
            return latency, False
    except Exception as e:
        print(f"Request {i} error: {e}")
        return time.perf_counter() - start_time, False

async def run_stress_test():
    async with httpx.AsyncClient() as client:
        tasks = []
        print(f"Starting stress test: {TOTAL_REQUESTS} total requests, {CONCURRENT_REQUESTS} concurrent.")
        
        start_test = time.perf_counter()
        
        # Simple semaphore to limit concurrency
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        
        async def sem_request(i):
            async with semaphore:
                return await make_request(client, i)

        results = await asyncio.gather(*[sem_request(i) for i in range(TOTAL_REQUESTS)])
        
        end_test = time.perf_counter()
        
        latencies = [r[0] for r in results if r[1]]
        failures = TOTAL_REQUESTS - len(latencies)
        
        print("\n--- Results ---")
        print(f"Total Time: {end_test - start_test:.2f}s")
        print(f"Successes: {len(latencies)}")
        print(f"Failures: {failures}")
        
        if latencies:
            print(f"Avg Latency: {statistics.mean(latencies):.2f}s")
            print(f"Min Latency: {min(latencies):.2f}s")
            print(f"Max Latency: {max(latencies):.2f}s")
            print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}s")
            print(f"Throughput: {len(latencies) / (end_test - start_test):.2f} req/s")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
