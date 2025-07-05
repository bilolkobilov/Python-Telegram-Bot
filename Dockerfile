FROM python:3.11-slim

# Install system dependencies including FFmpeg for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && playwright install --with-deps

COPY . .

CMD ["python", "main.py"]