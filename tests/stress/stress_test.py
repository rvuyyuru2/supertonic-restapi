import asyncio
import httpx
import time
import statistics
import random
from dataclasses import dataclass
from typing import List, Optional

API_URL = "http://localhost:8800/v1/audio/speech"
API_KEY = "rLKAAK9R8d2qiqZo7ijUvfEon-BwvupDzeBzJjMko_Q"
CONCURRENT_REQUESTS = 10
TOTAL_REQUESTS = 50

@dataclass
class RequestResult:
    is_stream: bool
    success: bool
    total_time: float
    ttfb: Optional[float] = None
    error: Optional[str] = None

async def make_request(client: httpx.AsyncClient, i: int, is_stream: bool) -> RequestResult:
    payload = {
        "input": "This is a stress test for Supertonic TTS API. It should handle multiple concurrent requests smoothly.",
        "voice": "alloy",
        "response_format": "mp3",
        "speed": 1.0,
        "stream": is_stream
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    start_time = time.perf_counter()
    
    try:
        if is_stream:
            # For streaming, we use client.stream to measure TTFB (Time To First Byte)
            async with client.stream("POST", API_URL, json=payload, headers=headers, timeout=60.0) as response:
                if response.status_code != 200:
                    return RequestResult(is_stream, False, time.perf_counter() - start_time, error=f"Status {response.status_code}")
                
                ttfb = None
                # Consume the stream
                async for chunk in response.aiter_bytes():
                    if ttfb is None:
                        ttfb = time.perf_counter() - start_time
                
                total_time = time.perf_counter() - start_time
                return RequestResult(is_stream, True, total_time, ttfb=ttfb)

        else:
            # For non-streaming, we wait for the full response
            response = await client.post(API_URL, json=payload, headers=headers, timeout=60.0)
            total_time = time.perf_counter() - start_time
            
            if response.status_code == 200:
                return RequestResult(is_stream, True, total_time, ttfb=total_time) # TTFB is same as total for non-stream
            else:
                return RequestResult(is_stream, False, total_time, error=f"Status {response.status_code}")

    except Exception as e:
        return RequestResult(is_stream, False, time.perf_counter() - start_time, error=str(e))

def print_stats(name: str, results: List[RequestResult]):
    if not results:
        print(f"\n--- {name} Results ---")
        print("No requests.")
        return

    latencies = [r.total_time for r in results]
    ttfbs = [r.ttfb for r in results if r.ttfb is not None]
    
    print(f"\n--- {name} Results ---")
    print(f"Total Requests: {len(results)}")
    
    if latencies:
        print(f"Avg Total Latency: {statistics.mean(latencies):.4f}s")
        print(f"P95 Total Latency: {statistics.quantiles(latencies, n=20)[18]:.4f}s")
    
    if ttfbs:
        print(f"Avg TTFB:          {statistics.mean(ttfbs):.4f}s")
        print(f"P95 TTFB:          {statistics.quantiles(ttfbs, n=20)[18]:.4f}s")

async def run_stress_test():
    # Increase limits for stress testing
    limits = httpx.Limits(max_keepalive_connections=CONCURRENT_REQUESTS, max_connections=CONCURRENT_REQUESTS)
    
    async with httpx.AsyncClient(limits=limits, timeout=120.0) as client:
        print(f"Starting stress test: {TOTAL_REQUESTS} requests, {CONCURRENT_REQUESTS} concurrent.")
        print("Mixing 50% Streaming and 50% Non-Streaming requests.")
        
        start_test = time.perf_counter()
        
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
        
        async def sem_request(i):
            async with semaphore:
                # Alternating or Random split
                is_stream = (i % 2 == 0)
                result = await make_request(client, i, is_stream)
                if not result.success:
                    print(f"Req {i} ({'Stream' if is_stream else 'Batch'}) failed: {result.error}")
                return result

        results = await asyncio.gather(*[sem_request(i) for i in range(TOTAL_REQUESTS)])
        
        end_test = time.perf_counter()
        total_duration = end_test - start_test
        
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        
        stream_results = [r for r in successes if r.is_stream]
        batch_results = [r for r in successes if not r.is_stream]
        
        print("\n" + "="*40)
        print("STRESS TEST COMPLETE")
        print("="*40)
        print(f"Duration:   {total_duration:.2f}s")
        print(f"Throughput: {len(successes) / total_duration:.2f} req/s")
        print(f"Successes:  {len(successes)}")
        print(f"Failures:   {len(failures)}")

        print_stats("STREAMING", stream_results)
        print_stats("NON-STREAMING", batch_results)

if __name__ == "__main__":
    asyncio.run(run_stress_test())
