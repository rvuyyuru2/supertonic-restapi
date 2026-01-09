FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (libsndfile for soundfile, build tools)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app directory
COPY app/ ./app/
# Copy scripts if needed or just use command


# Environment variables
ENV PORT=8800
ENV HOST=0.0.0.0
ENV MODEL_THREADS=1 
ENV MAX_WORKERS=4
ENV TIMEOUT=120
ENV PYTHONPATH=/app

EXPOSE 8800

# Start with Robyn
CMD ["sh", "-c", "robyn app/main.py --processes ${WEB_CONCURRENCY:-1} --workers ${WORKERS:-1}"]
