# Testing Supertonic TTS API

This guide covers how to test voice quality, system load, and load balancing.

## 1. Setup

Ensure you have your environment running with Docker Compose:

```bash
docker compose up -d
```
x
### Create an API Key
Before testing, you need an API key:
```bash
curl -X POST "http://localhost:8800/auth/create-key?name=Tester&price=15.0"
```
Copy the `api` value (the key) from the response.

## 2. Voice Quality Testing
This creates audio samples for all supported voices.

1. Open `tests/quality/generate_samples.py`.
2. Replace `YOUR_API_KEY_HERE` with your key.
3. Run the script:
   ```bash
   python3 tests/quality/generate_samples.py
   ```
4. Check `tests/samples/` for the audio files.

## 3. Load Balancing & Scaling
The `docker-compose.yml` includes an Nginx load balancer. You can scale the API service to multiple containers:

```bash
# Scale to 3 worker instances
docker compose up -d --scale api=3
```

Nginx will automatically distribute requests among the 3 containers. Check logs to see load distribution:
```bash
docker compose logs -f api
```

## 4. Stress Testing
This script hammers the API with concurrent requests to measure latency and throughput.

1. Open `tests/stress/stress_test.py`.
2. Replace `YOUR_API_KEY` with your key.
3. Install dependencies:
   ```bash
   pip install httpx
   ```
4. Run the test:
   ```bash
   python3 tests/stress/stress_test.py
   ```

You can adjust `CONCURRENT_REQUESTS` and `TOTAL_REQUESTS` in the script to increase the load.
