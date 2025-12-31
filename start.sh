#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Load environment variables
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

echo "Starting Supertonic TTS Production Server on $HOST:$PORT..."

# Point to app.main:app instead of main:app
exec gunicorn -k uvicorn.workers.UvicornWorker \
    -w 1 \
    --threads 4 \
    --timeout 300 \
    --bind $HOST:$PORT \
    app.main:app
