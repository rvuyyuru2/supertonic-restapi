import httpx
import asyncio
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "test" # Replace with valid key after creation
OUTPUT_DIR = "tests/output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

async def create_api_key():
    """Attempts to create an API key for testing"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/auth/create-key?name=ScenarioTester&price=15.0")
            if resp.status_code == 200:
                key = resp.json().get("api")
                logger.info(f"Created temporary API key: {key}")
                return key
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
    return None

async def test_simple_synthesis(api_key):
    """Scenario 1: Simple Usage"""
    logger.info("Testing: Simple Synthesis")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {
            "input": "This is a simple synthesis test from Supertonic API.",
            "voice": "alloy",
            "response_format": "wav",
            "stream": False
        }
        start = time.time()
        resp = await client.post(f"{API_BASE_URL}/v1/audio/speech", json=data, headers=headers, timeout=60.0)
        duration = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            output_path = f"{OUTPUT_DIR}/scenario_simple.wav"
            with open(output_path, "wb") as f:
                f.write(resp.content)
            logger.info(f"SUCCESS: Simple synthesis completed in {duration:.2f}ms. Saved to {output_path}")
        else:
            logger.error(f"FAILURE: Simple synthesis failed with {resp.status_code}: {resp.text}")

async def test_all_voices(api_key):
    """Scenario 2: Voice Styles"""
    logger.info("Testing: All Voices")
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Get list of voices
        voices_resp = await client.get(f"{API_BASE_URL}/voices", headers=headers)
        if voices_resp.status_code != 200:
            logger.error("Failed to fetch voices")
            return
        
        voices = voices_resp.json().get("voices", ["alloy", "echo", "fable", "onyx", "nova", "shimmer"])
        logger.info(f"Found voices: {voices}")
        
        for voice in voices[:3]: # Test a subset to be fast
            logger.info(f"  Testing voice: {voice}")
            data = {
                "input": f"Hello, I am using the {voice} voice style.",
                "voice": voice,
                "response_format": "mp3",
                "stream": False
            }
            resp = await client.post(f"{API_BASE_URL}/v1/audio/speech", json=data, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                output_path = f"{OUTPUT_DIR}/voice_{voice}.mp3"
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"  SUCCESS: {voice} saved to {output_path}")
            else:
                logger.error(f"  FAILURE: {voice} failed with {resp.status_code}")

async def test_speed_control(api_key):
    """Scenario 5: Speed Adjustment"""
    logger.info("Testing: Speed Control")
    speeds = [0.75, 1.0, 1.5]
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}
        for speed in speeds:
            logger.info(f"  Testing speed: {speed}x")
            data = {
                "input": "This is a speed control test. Testing different playback speeds.",
                "voice": "alloy",
                "speed": speed,
                "response_format": "wav",
                "stream": False
            }
            resp = await client.post(f"{API_BASE_URL}/v1/audio/speech", json=data, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                output_path = f"{OUTPUT_DIR}/speed_{speed}x.wav"
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"  SUCCESS: {speed}x saved to {output_path}")
            else:
                logger.error(f"  FAILURE: {speed}x failed with {resp.status_code}")

async def test_long_text_streaming(api_key):
    """Scenario 6: Long Text & Auto-Chunking (Streaming)"""
    logger.info("Testing: Long Text Streaming")
    long_text = (
        "This is a long text test to verify the auto-chunking and streaming capabilities of the Supertonic API. "
        "The server should split this text into smaller parts, synthesize them sequentially, and stream the results back to the client. "
        "This ensures low latency (Time To First Byte) even for very long inputs that would take a long time to synthesize fully. "
        "[pause:1.0] We also test if pause tags are handled correctly during streaming. "
        "The streaming flow should not block the event loop and should allow other requests to be processed concurrently."
    )
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {
            "input": long_text,
            "voice": "alloy",
            "response_format": "mp3",
            "stream": True
        }
        
        start_time = time.time()
        ttfb = None
        total_bytes = 0
        
        try:
            async with client.stream("POST", f"{API_BASE_URL}/v1/audio/speech", json=data, headers=headers, timeout=120.0) as response:
                if response.status_code != 200:
                    logger.error(f"Streaming failed: {response.status_code}")
                    return

                output_path = f"{OUTPUT_DIR}/scenario_long_stream.mp3"
                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        if ttfb is None:
                            ttfb = (time.time() - start_time) * 1000
                            logger.info(f"  TTFB: {ttfb:.2f}ms")
                        f.write(chunk)
                        total_bytes += len(chunk)
                
                total_time = (time.time() - start_time) * 1000
                logger.info(f"  SUCCESS: Streamed {total_bytes} bytes in {total_time:.2f}ms. Saved to {output_path}")
        except Exception as e:
            logger.error(f"Error during streaming: {e}")

async def main():
    logger.info("Starting Scenario-based Tests...")
    
    # Try to use existing key or create one
    api_key = os.environ.get("API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        api_key = await create_api_key()
    
    # if not api_key:
    #     logger.error("No API key available. Start the server and create a key.")
    #     return

    await test_simple_synthesis(api_key)
    await test_all_voices(api_key)
    await test_speed_control(api_key)
    await test_long_text_streaming(api_key)
    
    logger.info("All scenarios completed.")

if __name__ == "__main__":
    asyncio.run(main())
