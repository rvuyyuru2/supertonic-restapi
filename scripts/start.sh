#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# Project root is the parent of the script directory
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run ./scripts/setup.sh first."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
  set -a
  . .env
  set +a
fi

# Default values if not set in .env
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8800}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-2}
WORKERS=${WORKERS:-2}

# Export PYTHONPATH to include current directory for imports
export PYTHONPATH=$PYTHONPATH:.

echo "Starting Supertonic TTS Production Server on $HOST:$PORT with FastAPI..."

exec uvicorn app.main:app --host $HOST --port $PORT --workers $WORKERS
